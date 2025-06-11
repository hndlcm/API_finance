import requests
import time
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ⚙️ Авторизація до Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("../api-finanse-de717294db0b.json", scope)
client = gspread.authorize(creds)

# 📄 Відкриваємо таблицю
spreadsheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1Fg9Fo4TLqc0KYbC_GHBRccFZg8a5g9NJPfyMoSLSKM8/edit?usp=sharing"
)
worksheet = spreadsheet.worksheet("Аркуш1")

# 🔗 TRC20 API
address = "TRoJdqkhtJGpWVsvC67jk4Cp8FDAhQL1LE"
limit = 50
start = 0
row_data = []
all_transactions = []

while True:
    url = (
        f"https://apilist.tronscanapi.com/api/token_trc20/transfers"
        f"?limit={limit}&start={start}&relatedAddress={address}&confirm=true&filterTokenValue=1"
    )

    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Помилка при запиті: статус {response.status_code}")
        break

    data = response.json()
    transactions = data.get("token_transfers", [])

    if not transactions:
        print("✅ Усі TRC20 транзакції отримано.")
        break

    all_transactions.extend(transactions)

    for tx in transactions:
        timestamp = datetime.fromtimestamp(tx["block_ts"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        token = tx.get("token_info", {}).get("symbol", "")
        owner = tx.get("from_address", "")
        method = "TRC20"
        try:
            amount = float(tx.get("quant", 0)) / 10 ** int(tx.get("token_info", {}).get("decimals", 6))
        except Exception:
            amount = 0

        fee = 0  # TRC20 не повертає fee
        to_address = tx.get("to_address", "")
        tx_hash = tx.get("transaction_id", "")
        type_operation = "debit" if to_address == address else "credit"
        address_counterparty = to_address if type_operation=="credit" else tx.get("from_address", "")

        # A:Y — 25 колонок
        row = [""] * 25
        row[0] = timestamp
        row[1] = method
        row[3] = address
        row[4] = type_operation
        row[6] = amount
        row[7] = "USDT"
        row[8] = fee
        row[13] = address_counterparty
        row[16] = tx_hash

        row_data.append(row)

    print(f"🔄 Отримано {len(transactions)} транзакцій")
    start += limit
    time.sleep(0.4)

# 💾 Зберігаємо у файл
with open("trc20_transactions.json", "w", encoding="utf-8") as f:
    json.dump(all_transactions, f, ensure_ascii=False, indent=2)
print("💾 Дані збережено у файл trc20_transactions.json")

# --- Знаходимо перший вільний рядок ---
existing_records = len(worksheet.get_all_values())
start_row = existing_records + 1

# --- Ліміт рядків таблиці ---
MAX_ROWS = 1048576
if start_row + len(row_data) - 1 > MAX_ROWS:
    print("⚠️ Перевищено ліміт рядків таблиці. Обрізаємо.")
    row_data = row_data[:MAX_ROWS - start_row + 1]

# --- Розширення таблиці при потребі ---
required_rows = start_row + len(row_data) - 1
current_rows = worksheet.row_count

if required_rows > current_rows:
    worksheet.add_rows(required_rows - current_rows)

# --- Запис у таблицю ---
worksheet.update(
    values=row_data,
    range_name=f"A{start_row}:Y{start_row + len(row_data) - 1}"
)

print(f"\n📊 Успішно додано {len(row_data)} рядків у Google Таблицю починаючи з рядка {start_row}.")
