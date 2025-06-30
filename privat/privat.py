import time
import json
import requests
from datetime import datetime
from config import CONFIG
from table import init_google_sheet


BASE_URL = "https://acp.privatbank.ua/api/statements/transactions"


def fetch_transactions(api_token, start_date: str, end_date: str, limit: int = 100) -> list:
    headers = {
        "User-Agent": "MyApp/1.0",
        "token": api_token,
        "Content-Type": "application/json;charset=cp1251"
    }
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "limit": limit
    }
    all_transactions = []

    while True:
        response = requests.get(BASE_URL, headers=headers, params=params)

        if response.status_code != 200:
            print("❌ Помилка запиту:", response.status_code)
            print(response.text)
            break

        data = response.json()

        if data.get("status") != "SUCCESS":
            print("❌ API повернуло помилку:", data)
            break

        transactions = data.get("transactions", [])
        all_transactions.extend(transactions)

        print(f"✅ Отримано {len(transactions)} транзакцій")

        if data.get("exist_next_page"):
            params["followId"] = data.get("next_page_id", "")
        else:
            break

    print(f"\n📄 Загальна кількість транзакцій: {len(all_transactions)}")
    return all_transactions


def save_transactions_to_json(transactions: list, filename: str = "privat_transactions.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(transactions, f, ensure_ascii=False, indent=4)
    print(f"✅ Транзакції збережено у файл {filename}")


def write_privat_transactions_to_sheet(worksheet, transactions: list):
    try:
        existing_rows = worksheet.get_all_values()
    except Exception as e:
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

        datetime_str = f"{tx.get('DAT_KL', '')} {tx.get('TIM_P', '')}"
        try:
            tx_time = datetime.strptime(datetime_str, "%d.%m.%Y %H:%M")
            tx_time_str = tx_time.strftime("%d.%m.%Y %H:%M:%S")
        except Exception:
            tx_time_str = datetime_str.strip()

        new_row[0] = tx_time_str
        new_row[1] = "privatbank"
        new_row[3] = tx.get("AUT_MY_ACC", "")
        new_row[4] = "debit" if tx.get("TRANTYPE") == "D" else "credit"
        new_row[5] = float(tx.get("SUM", "0").replace(",", "."))
        new_row[6] = float(tx.get("SUM_E", "0").replace(",", "."))
        new_row[7] = tx.get("CCY", "UAH")
        new_row[10] = tx.get("OSND", "")
        new_row[11] = tx.get("AUT_CNTR_NAM", "")
        new_row[12] = tx.get("AUT_CNTR_CRF ", "")
        new_row[13] = tx.get("AUT_CNTR_ACC", "")
        new_row[14] = ""
        new_row[15] = ""
        new_row[16] = tx.get("ID", "")

        tx_id = new_row[16]
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


def privat_export(start_date="01-06-2025", end_date="20-06-2025"):
    tokens = CONFIG.get("PRIVAT", [])
    if not tokens:
        print("❌ У конфігурації немає PRIVAT токенів.")
        return

    worksheet = init_google_sheet()

    for entry in tokens:
        api_token = entry.get("api_token")
        if not api_token:
            continue
        print(f"🕐 Обробка токена PRIVAT...")
        transactions = fetch_transactions(api_token, start_date, end_date)
        save_transactions_to_json(transactions, filename="privat_transactions.json")
        write_privat_transactions_to_sheet(worksheet, transactions)



