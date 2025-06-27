import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def load_wallets(file_path="wallets.txt"):
    wallets = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            system, addresses = line.split("=", 1)
            wallets[system.strip().upper()] = [addr.strip() for addr in addresses.split(",") if addr.strip()]
    return wallets


def format_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M:%S")
    except Exception:
        return date_str


def export_fakturownia_invoices_to_google_sheets(worksheet, api_token=None):
    load_dotenv()
    API_TOKEN = api_token or os.getenv("FACTUROWNIA") or os.getenv("FACTUROWNIA") or os.getenv("FACTUROWNIA")
    BASE_URL = "https://orgwa.fakturownia.pl"

    def get_invoices(page=1):
        url = f"{BASE_URL}/invoices.json"
        params = {"api_token": API_TOKEN, "page": page}
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


def export_invoices_to_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("api-finanse-de717294db0b.json", scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1Fg9Fo4TLqc0KYbC_GHBRccFZg8a5g9NJPfyMoSLSKM8/edit?usp=sharing")
    worksheet = spreadsheet.worksheet("Аркуш1")

    wallets = load_wallets()

    if "FACTUROWNIA" in wallets:
        for token in wallets["FACTUROWNIA"]:
            print(f"Обробка токена: {token}")
            export_fakturownia_invoices_to_google_sheets(worksheet, api_token=token)



