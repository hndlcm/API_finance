import requests
import time
import json
import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- Налаштування Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("../api-finanse-de717294db0b.json", scope)
client = gspread.authorize(creds)

# Відкриваємо таблицю за URL та аркуш за назвою
spreadsheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1Fg9Fo4TLqc0KYbC_GHBRccFZg8a5g9NJPfyMoSLSKM8/edit?usp=sharing"
)
worksheet = spreadsheet.worksheet("Аркуш1")

# --- Налаштування Etherscan ---
load_dotenv()
api_key = os.getenv("ETHER")

address = "0x19Cf249E7e423b5Bd2d41FD62e7f3adbfdEe5B47"  # Ваша адреса
start_block = 0
end_block = 99999999
page = 1
offset = 100
all_transactions = []

while True:
    url = (
        f"https://api.etherscan.io/api"
        f"?module=account"
        f"&action=tokentx"  # транзакції ERC20 токенів
        f"&address={address}"
        f"&startblock={start_block}"
        f"&endblock={end_block}"
        f"&page={page}"
        f"&offset={offset}"
        f"&sort=asc"
        f"&apikey={api_key}"
    )

    response = requests.get(url)
    if response.status_code != 200:
        print("❌ Помилка при запиті:", response.status_code)
        break

    result = response.json()
    transactions = result.get("result", [])

    if not transactions:
        print("✅ Усі транзакції отримано.")
        break

    all_transactions.extend(transactions)
    print(f"🔄 Сторінка {page}: Отримано {len(transactions)} транзакцій (всього: {len(all_transactions)})")

    page += 1
    time.sleep(0.3)

# --- Зберігаємо транзакції у JSON файл ---
with open("erc20_transactions.json", "w", encoding="utf-8") as f:
    json.dump(all_transactions, f, ensure_ascii=False, indent=4)

print("💾 Транзакції успішно збережено у файл erc20_transactions.json")

# --- Формування даних для Google Sheets ---
row_data = []

for tx in all_transactions:
    timestamp = datetime.fromtimestamp(int(tx["timeStamp"])).strftime("%Y-%m-%d %H:%M:%S")

    token_symbol = tx.get("tokenSymbol", "UNKNOWN")
    token_decimal = int(tx.get("tokenDecimal", "18"))

    from_address = tx.get("from", "")
    to_address = tx.get("to", "")
    tx_hash = tx.get("hash", "")

    try:
        amount = int(tx.get("value", "0")) / (10 ** token_decimal)
    except Exception:
        amount = 0

    try:
        gas_used = int(tx.get("gasUsed", "0"))
        gas_price = int(tx.get("gasPrice", "0"))
        fee = (gas_used * gas_price) / 10 ** 18
    except Exception:
        fee = 0

    type_operation = "debit" if to_address.lower() == address.lower() else "credit"
    address_counterparty = to_address if type_operation == "credit" else from_address

    # Підготовка рядка з 25 колонками (A-Y)
    row = [""] * 25
    row[0] = timestamp
    row[1] = "ERC20"
    row[3] = address
    row[4] = type_operation
    row[6] = amount
    row[7] = token_symbol
    row[13] = address_counterparty
    row[16] = tx_hash

    row_data.append(row)

# --- Знаходимо перший вільний рядок, щоб не перезаписувати дані ---
existing_records = len(worksheet.get_all_values())
start_row = existing_records + 1

# --- Записуємо дані у Google Таблицю ---
if row_data:
    worksheet.update(f"A{start_row}:Y{start_row + len(row_data) - 1}", row_data)
    print(f"\n📊 Успішно додано {len(row_data)} рядків у Google Таблицю починаючи з рядка {start_row}.")
else:
    print("⚠️ Немає нових транзакцій для запису.")
