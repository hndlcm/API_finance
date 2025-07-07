import requests
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config_manager import CONFIG


def format_amount(value):
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.00


def format_date(date_str):
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return date_str


def export_bitfactura_invoices_to_google_sheets(worksheet, api_token, from_date=None, to_date=None):
    BASE_URL = "https://handleua.bitfaktura.com.ua"

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

            if from_date or to_date:
                filtered = []
                for inv in invoices:
                    updated = inv.get("updated_at", "")
                    if updated:
                        inv_date = datetime.fromisoformat(updated.replace("Z", "+00:00")).date()
                        if from_date and inv_date < from_date:
                            continue
                        if to_date and inv_date > to_date:
                            continue
                    filtered.append(inv)
                invoices = filtered

            all_invoices.extend(invoices)
            print(f"✅ Отримано сторінку {page} — {len(invoices)} інвойсів")

            if len(invoices) < 100:
                break
            page += 1
        return all_invoices

    invoices = get_all_invoices()

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
        row[0] = format_date(invoice.get("created_at", ""))
        row[1] = "bitfaktura"
        row[3] = invoice.get("seller_bank_account", "")
        row[4] = "invoice"
        amount = invoice.get("price_gross", 0)
        row[5] = format_amount(amount)
        row[6] = format_amount(amount)
        row[7] = invoice.get("currency", "")
        row[10] = invoice.get("number", "")
        row[11] = invoice.get("buyer_name", "")
        row[12] = int(invoice.get("buyer_tax_no", ""))
        row[13] = invoice.get("buyer_bank_account", "")
        row[16] = int(invoice.get("id", ""))

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


def export_bitfactura_all_to_google_sheets():
    sheet_conf = CONFIG["google_sheet"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(sheet_conf["credentials_path"], scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(sheet_conf["spreadsheet_url"])
    worksheet = spreadsheet.worksheet(sheet_conf["worksheet_name"])

    bitfactura_entries = CONFIG.get("BITFACTURA", [])
    if not bitfactura_entries:
        print("⚠️ Немає підключених Bitfaktura акаунтів у конфігурації.")
        return

    for entry in bitfactura_entries:
        token = entry.get("api_token")
        days = entry.get("days", 5)

        from_date = datetime.now().date() - timedelta(days=days)
        to_date = datetime.now().date()

        print(f"📡 Обробка токена: {token[:6]}..., діапазон дат: {from_date} - {to_date}")
        export_bitfactura_invoices_to_google_sheets(worksheet, token, from_date=from_date, to_date=to_date)
