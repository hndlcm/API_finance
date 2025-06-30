import requests
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import CONFIG


def format_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M:%S")
    except Exception:
        return date_str


def export_fakturownia_invoices_to_google_sheets(worksheet, api_token):
    BASE_URL = "https://orgwa.fakturownia.pl"

    def get_invoices(page=1):
        url = f"{BASE_URL}/invoices.json"
        params = {"api_token": api_token, "page": page}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print("❌ Помилка:", response.status_code, response.text)
            return []

    def get_all_invoices():
        all_invoices = []
        page = 1
        while True:
            invoices = get_invoices(page)
            if not invoices:
                break
            all_invoices.extend(invoices)
            print(f"✅ Отримано сторінку {page} — {len(invoices)} інвойсів")
            page += 1
        return all_invoices

    invoices = get_all_invoices()

    with open("fakturownia_invoices.json", "w", encoding="utf-8") as f:
        json.dump(invoices, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Збережено {len(invoices)} інвойсів у файл 'fakturownia_invoices.json'")

    existing_rows = worksheet.get_all_values()
    header_offset = 1
    existing_invoices_by_id = {}
    for i, row in enumerate(existing_rows[header_offset:], start=header_offset + 1):
        full_row = row + [""] * (17 - len(row))
        inv_id = full_row[16]
        if inv_id:
            existing_invoices_by_id[inv_id] = {"row_number": i, "row_data": full_row}

    rows_to_update = []
    rows_to_append = []

    for invoice in invoices:
        row = [""] * 17
        row[0] = format_date(invoice.get("updated_at", ""))
        row[1] = "fakturownia"
        row[3] = invoice.get("seller_bank_account", "")
        row[4] = "invoice"
        amount = invoice.get("price_gross", 0)
        row[5] = float(amount)
        row[6] = float(amount)
        row[7] = invoice.get("currency", "")
        row[10] = invoice.get("number", "")
        row[11] = invoice.get("client_name", "")
        row[12] = invoice.get("client_tax_no", "")
        row[13] = invoice.get("client_bank_account", "")
        row[16] = str(invoice.get("id", ""))

        inv_id = row[16]
        if inv_id in existing_invoices_by_id:
            existing = existing_invoices_by_id[inv_id]
            if row != existing["row_data"]:
                rows_to_update.append((existing["row_number"], row))
        else:
            rows_to_append.append(row)

    for row_number, row_data in rows_to_update:
        worksheet.update(f"A{row_number}:Q{row_number}", [row_data])
        print(f"🔁 Оновлено інвойс у рядку {row_number}")

    if rows_to_append:
        start_row = len(existing_rows) + 1
        worksheet.update(f"A{start_row}:Q{start_row + len(rows_to_append) - 1}", rows_to_append)
        print(f"➕ Додано {len(rows_to_append)} нових інвойсів з рядка {start_row}")
    else:
        print("✅ Нових інвойсів для додавання немає.")


def export_fakturownia_all_to_google_sheets():
    sheet_conf = CONFIG["google_sheet"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(sheet_conf["credentials_path"], scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(sheet_conf["spreadsheet_url"])
    worksheet = spreadsheet.worksheet(sheet_conf["worksheet_name"])

    fakturownia_entries = CONFIG.get("FACTUROWNIA", [])
    if not fakturownia_entries:
        print("⚠️ Немає токенів Fakturownia в конфігурації.")
        return

    for entry in fakturownia_entries:
        token = entry["api_token"]
        print(f"📡 Обробка токена: {token[:6]}...")  # Безпечно обрізати токен
        export_fakturownia_invoices_to_google_sheets(worksheet, token)


