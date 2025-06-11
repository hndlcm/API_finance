import requests
import json
import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Завантаження токенів ---
load_dotenv()
API_TOKEN = os.getenv("FACTUROW")
BASE_URL = "https://orgwa.fakturownia.pl"

# --- Google Sheets авторизація ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("../api-finanse-de717294db0b.json", scope)
client = gspread.authorize(creds)

# Відкриття таблиці та аркушу
spreadsheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1Fg9Fo4TLqc0KYbC_GHBRccFZg8a5g9NJPfyMoSLSKM8/edit?usp=sharing"
)
worksheet = spreadsheet.worksheet("Аркуш1")

# --- Отримання однієї сторінки інвойсів ---
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

# --- Отримання всіх інвойсів по сторінках ---
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

# --- Основний блок ---
if __name__ == "__main__":
    invoices = get_all_invoices()

    # 💾 Збереження у файл
    with open("invoices.json", "w", encoding="utf-8") as f:
        json.dump(invoices, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Збережено {len(invoices)} інвойсів у файл 'invoices.json'")

    # --- Підготовка даних до запису ---
    row_data = []
    for invoice in invoices:
        row = [""] * 16
        row[0] = invoice.get("issue_date", "")
        row[1] = "fakturownia"
        row[3] = invoice.get("seller_bank_account", "")
        row[4] = "invoice"
        row[5] = invoice.get("price_gross", "")
        row[6] = invoice.get("price_gross", "")
        row[7] = invoice.get("currency", "")
        row[10] = invoice.get("number", "")
        row[11] = invoice.get("client_name", "")
        row[12] = invoice.get("client_tax_no", "")
        row[13] = invoice.get("client_bank_account", "")
        row[15] = invoice.get("id", "")
        row_data.append(row)

    # --- Додавання в Google Таблицю (в кінець) ---
    existing_records = len(worksheet.get_all_values())
    start_row = existing_records + 1
    worksheet.update(f"A{start_row}:P{start_row + len(row_data) - 1}", row_data)

    print(f"\n📊 Успішно додано {len(row_data)} інвойсів у Google Таблицю з рядка {start_row}.")
