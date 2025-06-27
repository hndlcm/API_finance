import os
import time
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from table import init_google_sheet

load_dotenv()

TOKEN = os.getenv('MONO')
BASE_URL = 'https://api.monobank.ua/personal/statement/{account}/{from_time}/{to_time}'
HEADERS = {'X-Token': TOKEN}


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


def info_client():
    URL = 'https://api.monobank.ua/personal/client-info'
    response = requests.get(URL, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        with open('monobank_client_info.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print("✅ Дані збережено в monobank_client_info.json")
        return data
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return None


def get_monobank_statements(account, from_time, to_time):
    all_transactions = []
    while True:
        url = BASE_URL.format(account=account, from_time=from_time, to_time=to_time)
        print(f"GET: {url}")
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text}")
            break
        transactions = response.json()
        all_transactions.extend(transactions)
        if len(transactions) < 500:
            break
        last_tx_time = transactions[-1]['time']
        to_time = last_tx_time
        time.sleep(60)
    return all_transactions


def save_monobank_transactions_to_json(account_id, days_back=183, filename='monobank_transactions.json'):
    current_time = int(time.time())
    from_time = current_time - days_back * 24 * 60 * 60
    to_time = current_time
    max_range_seconds = 2682000  # 31 день + 1 година

    all_transactions = []
    print(f"📅 Починаємо завантаження транзакцій за останні {days_back} днів...")

    while from_time < to_time:
        chunk_to_time = min(from_time + max_range_seconds, to_time)
        print(f"📦 Отримуємо транзакції з {datetime.fromtimestamp(from_time)} до {datetime.fromtimestamp(chunk_to_time)}")
        try:
            chunk_transactions = get_monobank_statements(account_id, from_time, chunk_to_time)
            all_transactions.extend(chunk_transactions)
        except Exception as e:
            print(f"❌ Помилка при запиті: {e}")
            break
        from_time = chunk_to_time
        if from_time < to_time:
            print("⏳ Очікуємо 60 секунд через ліміт Mono API...")
            time.sleep(60)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_transactions, f, ensure_ascii=False, indent=4)

    print(f"✅ Успішно збережено {len(all_transactions)} транзакцій у {filename}")
    return all_transactions


def write_monobank_transactions_to_sheet(account_id, worksheet, transactions: list):
    try:
        existing_rows = worksheet.get_all_values()
    except Exception:
        print("⚠️ Зачекай 60 секунд (Rate Limit)...")
        time.sleep(60)
        existing_rows = worksheet.get_all_values()

    header_offset = 1
    existing_tx_by_id = {}
    for i, row in enumerate(existing_rows[header_offset:], start=header_offset + 1):
        if len(row) > 16 and row[16]:
            existing_tx_by_id[row[16]] = {"row_number": i, "row_data": row + [""] * (25 - len(row))}

    rows_to_update = []
    rows_to_append = []

    for tx in transactions:
        new_row = [""] * 25
        tx_time = datetime.fromtimestamp(tx.get("time", 0)).strftime("%d.%m.%Y %H:%M:%S")
        description = tx.get("description", "")
        amount = tx.get("amount", 0)
        currency_code = tx.get("currencyCode", 980)
        mcc = tx.get("mcc", "")
        balance = tx.get("balance", 0)
        tx_id = tx.get("id", "")

        new_row[0] = tx_time
        new_row[1] = "monobank"
        new_row[3] = account_id
        new_row[4] = "debit" if amount < 0 else "credit"
        new_row[5] = abs(amount) / 100
        new_row[6] = abs(amount) / 100
        new_row[7] = "UAH" if currency_code == 980 else str(currency_code)
        new_row[8] = 0
        new_row[9] = balance / 100
        new_row[10] = tx.get("comment", "")
        new_row[11] = tx.get("counterName", "")
        new_row[12] = tx.get("counterEdrpou", "")
        new_row[13] = tx.get("counterIban", "")
        new_row[14] = mcc
        new_row[15] = description
        new_row[16] = tx_id

        if tx_id in existing_tx_by_id:
            existing = existing_tx_by_id[tx_id]
            if new_row != existing["row_data"]:
                rows_to_update.append((existing["row_number"], new_row))
        else:
            rows_to_append.append(new_row)

    if rows_to_update:
        batch_data = [{"range": f"A{row_number}:Y{row_number}", "values": [row_data]} for row_number, row_data in rows_to_update]
        worksheet.batch_update(batch_data)
        print(f"🔁 Оновлено {len(rows_to_update)} транзакцій.")

    if rows_to_append:
        start_row = len(existing_rows) + 1
        worksheet.update(f"A{start_row}:Y{start_row + len(rows_to_append) - 1}", rows_to_append)
        print(f"➕ Додано {len(rows_to_append)} нових транзакцій починаючи з рядка {start_row}.")
    else:
        print("✅ Нових транзакцій немає.")


def mono():
    wallets = load_wallets()
    if "MONO" not in wallets:
        print("❌ У wallets.txt немає запису MONO")
        return

    worksheet = init_google_sheet()  # Припускаю, що ти так ініціалізуєш лист

    client_info = info_client()
    if not client_info:
        print("❌ Не вдалося отримати інформацію про клієнта.")
        return

    accounts = client_info.get("accounts", [])
    if not accounts:
        print("❌ У клієнта не знайдено жодного рахунку.")
        return

    for account in accounts:
        account_id = account.get("id")
        iban = account.get("iban", "")
        if not account_id:
            print("❌ Не вдалося отримати ID рахунку.")
            continue

        print(f"\n📘 Опрацьовується рахунок: {account_id}")
        transactions = save_monobank_transactions_to_json(account_id=account_id, days_back=183, filename=f"mono_{account_id}.json")
        write_monobank_transactions_to_sheet(iban, worksheet, transactions)



