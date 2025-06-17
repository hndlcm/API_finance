from datetime import datetime

import requests
import json
import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def export_bitfactura_invoices_to_google_sheets():
    load_dotenv()
    API_TOKEN = os.getenv("BITFACTURA")
    BASE_URL = "https://handleua.bitfaktura.com.ua"

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("api-finanse-de717294db0b.json", scope)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1Fg9Fo4TLqc0KYbC_GHBRccFZg8a5g9NJPfyMoSLSKM8/edit?usp=sharing"
    )
    worksheet = spreadsheet.worksheet("Аркуш1")

    def get_invoices(page=1):
        url = f"{BASE_URL}/invoices.json"
        params = {
            "api_token": API_TOKEN,
            "page": page
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print("❌ Помилка:", response.status_code, response.text)
            return []

    invoices = get_invoices()

    with open("invoices.json", "w", encoding="utf-8") as f:
        json.dump(invoices, f, ensure_ascii=False, indent=2)
    print(f"✅ Збережено {len(invoices)} інвойсів у файл invoices.json")

    # Отримуємо всі існуючі рядки (включно з заголовком)
    existing_rows = worksheet.get_all_values()
    header_offset = 1  # Якщо є заголовок, інакше 0

    # Створюємо словник існуючих інвойсів за ID (колонка Q - індекс 16)
    existing_invoices_by_id = {}
    for i, row in enumerate(existing_rows[header_offset:], start=header_offset + 1):
        full_row = row + [""] * (17 - len(row))  # Заповнюємо до 17 колонок
        inv_id = full_row[16]
        if inv_id:
            existing_invoices_by_id[inv_id] = {"row_number": i, "row_data": full_row}

    rows_to_update = []
    rows_to_append = []


    for invoice in invoices:
        row = [""] * 17
        dt = datetime.fromisoformat(invoice.get("updated_at", ""))

        # Перетворюємо у формат без часового поясу
        formatted = dt.strftime("%Y.%m.%d %H:%M:%S")
        row[0] = formatted
        row[1] = "fakturownia"
        row[3] = invoice.get("seller_bank_account", "")
        row[4] = "invoice"
        amount = str(invoice.get("price_gross", "")).replace(".", ",")
        row[5] = amount
        row[6] = amount
        row[7] = invoice.get("currency", "")
        row[10] = invoice.get("number", "")
        row[11] = invoice.get("buyer_name", "")
        row[12] = invoice.get("buyer_tax_no", "")
        row[13] = invoice.get("buyer_bank_account", "")
        row[16] = str(invoice.get("id", ""))

        inv_id = row[16]

        if inv_id in existing_invoices_by_id:
            existing = existing_invoices_by_id[inv_id]
            if row != existing["row_data"]:
                rows_to_update.append((existing["row_number"], row))
        else:
            rows_to_append.append(row)

    # Оновлення існуючих рядків
    for row_number, row_data in rows_to_update:
        worksheet.update(f"A{row_number}:Q{row_number}", [row_data])
        print(f"🔁 Оновлено інвойс у рядку {row_number}")

    # Додавання нових рядків у кінець таблиці
    if rows_to_append:
        start_row = len(existing_rows) + 1
        worksheet.update(f"A{start_row}:Q{start_row + len(rows_to_append) - 1}", rows_to_append)
        print(f"➕ Додано {len(rows_to_append)} нових інвойсів починаючи з рядка {start_row}.")
    else:
        print("✅ Нових інвойсів для додавання немає.")

"""if __name__ == "__main__":
    export_bitfactura_invoices_to_google_sheets()"""
