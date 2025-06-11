import requests
import json
import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Завантаження .env і BitFaktura токену ---
load_dotenv()
API_TOKEN = os.getenv("BITFACTURA")
BASE_URL = "https://handleua.bitfaktura.com.ua"

# --- Авторизація Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("../api-finanse-de717294db0b.json", scope)
client = gspread.authorize(creds)

# Відкриваємо таблицю і аркуш
spreadsheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1Fg9Fo4TLqc0KYbC_GHBRccFZg8a5g9NJPfyMoSLSKM8/edit?usp=sharing"
)
worksheet = spreadsheet.worksheet("Аркуш1")

# --- Отримання інвойсів ---
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

# --- Збереження у файл JSON ---
with open("invoices.json", "w", encoding="utf-8") as f:
    json.dump(invoices, f, ensure_ascii=False, indent=2)
print(f"✅ Збережено {len(invoices)} інвойсів у файл invoices.json")

# --- Підготовка до запису у Google Sheets ---
row_data = []
for invoice in invoices:
    row = [""] * 16
    row[0] = invoice.get("issue_date", "")
    row[1] = "bitfactura"
    row[3] = invoice.get("seller_bank_account", "")
    row[4] = "invoice"
    row[5] = invoice.get("price_gross", "")
    row[6] = invoice.get("price_gross", "")
    row[7] = invoice.get("currency", "")
    row[10] = invoice.get("number", "")
    row[11] = invoice.get("buyer_name", "")
    row[12] = invoice.get("buyer_tax_no", "")
    row[13] = invoice.get("buyer_bank_account", "")
    row[15] = invoice.get("id", "")

    row_data.append(row)

# --- Знаходимо останній вільний рядок ---
existing_records = len(worksheet.get_all_values())
start_row = existing_records + 1

# --- Запис у Google Таблицю ---
worksheet.update(f"A{start_row}:P{start_row + len(row_data) - 1}", row_data)
print(f"\n📊 Успішно додано {len(row_data)} інвойсів у таблицю з рядка {start_row}.")
