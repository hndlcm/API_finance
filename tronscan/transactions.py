import requests
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ⚙️ Налаштування доступу до Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("../api-finanse-de717294db0b.json", scope)
client = gspread.authorize(creds)

# Відкриваємо таблицю за URL та аркуш за назвою
spreadsheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1Fg9Fo4TLqc0KYbC_GHBRccFZg8a5g9NJPfyMoSLSKM8/edit?usp=sharing"
)
worksheet = spreadsheet.worksheet("Аркуш1")

# Адреса для запиту транзакцій TRON
address = "TRoJdqkhtJGpWVsvC67jk4Cp8FDAhQL1LE"
limit = 50
start = 0
row_data = []

while True:
    url = (
        f"https://apilist.tronscan.org/api/transaction"
        f"?sort=-timestamp&count=true&limit={limit}&start={start}&address={address}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Помилка при запиті: статус {response.status_code}")
        break

    data = response.json()
    transactions = data.get("data", [])

    if not transactions:
        print("✅ Усі транзакції отримано.")
        break

    for tx in transactions:
        # Форматування timestamp
        timestamp = datetime.fromtimestamp(tx["timestamp"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        token = tx.get("tokenType", "")
        owner = tx.get("ownerAddress", "")
        method = tx.get("trigger_info", {}).get("methodName", "")

        value_raw = tx.get("trigger_info", {}).get("parameter", {}).get("_value")
        try:
            amount = int(value_raw) / 1_000_000 if value_raw else int(tx.get("amount", "0")) / 1_000_000
        except Exception:
            amount = 0

        try:
            fee = int(tx.get("cost", {}).get("fee", 0)) / 1_000_000
        except Exception:
            fee = 0

        to_address = tx.get("toAddress", "")
        tx_hash = tx.get("hash", "")

        # Підготовка рядка з 25 колонками (A-Y)
        row = [""] * 25
        row[0] = timestamp  # A
        row[1] = token      # B
        row[3] = owner      # D
        row[4] = method     # E
        row[6] = amount     # G
        row[8] = fee        # I
        row[13] = to_address  # N
        row[16] = tx_hash     # Q

        row_data.append(row)

    print(f"🔄 Отримано {len(transactions)} транзакцій")
    start += limit
    time.sleep(0.4)

# --- Знаходимо перший вільний рядок, щоб не перезаписувати дані ---
existing_records = len(worksheet.get_all_values())
start_row = existing_records + 1  # записуємо після останнього рядка

# --- Записуємо дані, починаючи з start_row ---
worksheet.update(f"A{start_row}:Y{start_row + len(row_data) - 1}", row_data)

print(f"\n📊 Успішно додано {len(row_data)} рядків у Google Таблицю починаючи з рядка {start_row}.")
