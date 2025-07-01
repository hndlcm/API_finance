import time
import json
import requests
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import CONFIG


def format_date(timestamp):
    try:
        return datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M:%S")
    except Exception:
        return ""


def init_google_sheet():
    sheet_conf = CONFIG["google_sheet"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(sheet_conf["credentials_path"], scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(sheet_conf["spreadsheet_url"])
    worksheet = spreadsheet.worksheet(sheet_conf["worksheet_name"])
    return worksheet


def info_client(api_token):
    url = "https://api.monobank.ua/personal/client-info"
    headers = {"X-Token": api_token}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        with open('monobank_client_info.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print("✅ Дані клієнта збережено у monobank_client_info.json")
        return data
    else:
        print(f"❌ Помилка при отриманні info: {response.status_code} {response.text}")
        return None


def get_monobank_statements(api_token, account, from_time, to_time):
    url = f'https://api.monobank.ua/personal/statement/{account}/{from_time}/{to_time}'
    headers = {'X-Token': api_token}
    print(f"GET: {url}")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Помилка {response.status_code}: {response.text}")
        return []
    return response.json()


def save_monobank_transactions_to_json(api_token, account_id, from_time, to_time, filename=None):
    max_range_seconds = 2682000  # 31 днів
    all_transactions = []

    print(f"📅 Завантаження транзакцій з {datetime.fromtimestamp(from_time)} до {datetime.fromtimestamp(to_time)}")

    while from_time < to_time:
        chunk_to_time = min(from_time + max_range_seconds, to_time)
        print(f"📦 Отримуємо транзакції з {datetime.fromtimestamp(from_time)} до {datetime.fromtimestamp(chunk_to_time)}")
        chunk_transactions = get_monobank_statements(api_token, account_id, from_time, chunk_to_time)
        if not chunk_transactions:
            break
        all_transactions.extend(chunk_transactions)
        from_time = chunk_to_time
        if from_time < to_time:
            print("⏳ Очікуємо 60 секунд через ліміт Mono API...")
            time.sleep(60)

    filename = filename or f"mono_{account_id}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_transactions, f, ensure_ascii=False, indent=4)

    print(f"✅ Збережено {len(all_transactions)} транзакцій у {filename}")
    return all_transactions


def write_monobank_transactions_to_sheet(account_id, worksheet, transactions):
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
        tx_time = format_date(tx.get("time", 0))
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


def mono_export():
    tokens = CONFIG.get("MONO", [])
    if not tokens:
        print("❌ У конфігурації немає MONO токенів.")
        return

    worksheet = init_google_sheet()

    for entry in tokens:
        api_token = entry.get("api_token")
        if not api_token:
            continue

        # 🕒 Отримати дату з конфігу
        date_str = entry.get("data")  # наприклад: "01.07.2025"
        try:
            dt = datetime.strptime(date_str, "%d.%m.%Y")
        except Exception:
            print(f"❌ Невірний формат дати: {date_str}")
            continue

        from_time = int(dt.timestamp())
        to_time = int((dt + timedelta(days=1)).timestamp())

        client_info = info_client(api_token)
        if not client_info:
            print("❌ Не вдалося отримати інформацію про клієнта.")
            continue

        accounts = client_info.get("accounts", [])
        if not accounts:
            print("❌ У клієнта немає рахунків.")
            continue

        for account in accounts:
            account_id = account.get("id")
            iban = account.get("iban", "")
            if not account_id:
                print("❌ Не вдалося отримати ID рахунку.")
                continue

            print(f"\n📘 Опрацьовується рахунок: {account_id} (IBAN: {iban})")
            transactions = save_monobank_transactions_to_json(
                api_token, account_id, from_time, to_time, filename=f"mono_{account_id}.json"
            )
            write_monobank_transactions_to_sheet(iban, worksheet, transactions)

        # 🗓️ Оновлення дати в пам'яті (не зберігається у файл)
        next_day = (dt + timedelta(days=1)).strftime("%d.%m.%Y")
        entry["data"] = next_day
        print(f"📆 Наступна дата: {next_day}")


if __name__ == "__main__":
    mono_export()
