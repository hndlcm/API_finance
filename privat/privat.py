import time
import json
import requests
from datetime import datetime, timedelta
from table import init_google_sheet
from config_manager import CONFIG, config_manager  

BASE_URL_TRANSACTIONS = "https://acp.privatbank.ua/api/statements/transactions"
BASE_URL_BALANCES = "https://acp.privatbank.ua/api/statements/balance/final"


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
        response = requests.get(BASE_URL_TRANSACTIONS, headers=headers, params=params)
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


def fetch_balances(api_token: str) -> list:
    headers = {
        "User-Agent": "MyApp/1.0",
        "token": api_token,
        "Content-Type": "application/json;charset=cp1251"
    }
    params = {"limit": 100}
    all_balances = []

    while True:
        response = requests.get(BASE_URL_BALANCES, headers=headers, params=params)
        if response.status_code != 200:
            print("❌ Помилка запиту balance:", response.status_code)
            print(response.text)
            break

        data = response.json()
        if data.get("status") != "SUCCESS":
            print("❌ API balance повернуло помилку:", data)
            break

        balances = data.get("balances", [])
        all_balances.extend(balances)

        print(f"📊 Отримано {len(balances)} балансів")

        if data.get("exist_next_page"):
            params["followId"] = data.get("next_page_id", "")
        else:
            break

    return all_balances


def write_privat_transactions_to_sheet(worksheet, transactions: list, acc_name_map: dict, acc_balance_map: dict):
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

        datetime_str = f"{tx.get('DAT_KL', '')} {tx.get('TIM_P', '')}"
        try:
            tx_time = datetime.strptime(datetime_str, "%d.%m.%Y %H:%M")
            tx_time_str = tx_time.strftime("%d.%m.%Y %H:%M:%S")
        except Exception:
            tx_time_str = datetime_str.strip()

        account = tx.get("AUT_MY_ACC", "")
        new_row[0] = tx_time_str
        new_row[1] = "privatbank"
        new_row[2] = acc_name_map.get(account, "")  # назва рахунку
        new_row[3] = account
        new_row[4] = "debit" if tx.get("TRANTYPE") == "D" else "credit"
        try:
            new_row[5] = float(tx.get("SUM", "0").replace(",", "."))
        except Exception:
            new_row[5] = 0.0
        try:
            new_row[6] = float(tx.get("SUM_E", "0").replace(",", "."))
        except Exception:
            new_row[6] = 0.0
        
        new_row[7] = tx.get("CCY", "UAH")
        new_row[9] = acc_balance_map.get(account, "")  # баланс із balanceInEq
        new_row[10] = tx.get("OSND", "")
        new_row[11] = tx.get("AUT_CNTR_NAM", "")
        new_row[12] = (
            tx.get("AUT_CNTR_CRF") or
            tx.get("PAYER_ULTMT_NCEO") or
            tx.get("RECIPIENT_ULTMT_NCEO") or
            ""
        )
        new_row[13] = tx.get("AUT_CNTR_ACC", "")
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


def update_balances_in_sheet(worksheet, balances: list):
    print("\n📊 Оновлення балансів у таблиці...")
    existing_rows = worksheet.get_all_values()

    acc_col = 3       # колонка з рахунком в таблиці (D)
    balance_col = 9   # колонка для балансу (J)

    rows_to_update = []

    acc_to_row = {}
    for i, row in enumerate(existing_rows):
        if len(row) > acc_col and row[acc_col]:
            acc_to_row[row[acc_col]] = i + 1  # номер рядка для оновлення

    for bal in balances:
        acc = bal.get("acc", "")
        balance = bal.get("balanceInEq", "0.00")  # беремо balanceInEq
        if acc in acc_to_row:
            row_number = acc_to_row[acc]
            rows_to_update.append({
                "range": f"{chr(ord('A') + balance_col)}{row_number}",
                "values": [[balance]]
            })
            print(f"Оновлено баланс (balanceInEq) для рахунку {acc}: {balance}")

    if rows_to_update:
        worksheet.batch_update(rows_to_update)
        print(f"✅ Оновлено баланси у {len(rows_to_update)} рядках.")
    else:
        print("⚠️ Не знайдено рахунків для оновлення балансу.")


def privat_export():
    tokens = CONFIG.get("PRIVAT", [])
    if not tokens:
        print("❌ У конфігурації немає PRIVAT токенів.")
        return

    worksheet = init_google_sheet()

    for entry in tokens:
        api_token = entry.get("api_token")
        date_str = entry.get("data")

        if not api_token:
            print("⚠️ Пропущено через відсутність токена")
            continue

        try:
            config_date = datetime.strptime(date_str, "%d.%m.%Y") if date_str else datetime.now()
        except Exception:
            print(f"❌ Невірний формат дати в конфігу: {date_str}, використовую сьогоднішню дату")
            config_date = datetime.now()

        from_date = (config_date - timedelta(days=5)).strftime("%d-%m-%Y")
        to_date = datetime.now().strftime("%d-%m-%Y")

        print(f"\n📆 Обробка транзакцій з {from_date} до {to_date}")

        transactions = fetch_transactions(api_token, from_date, to_date)

        print("📈 Отримання фінальних балансів...")
        balances = fetch_balances(api_token)

        # Словник: рахунок → імʼя
        acc_name_map = {b.get("acc"): b.get("nameACC") for b in balances}
        # Словник: рахунок → баланс (balanceInEq)
        acc_balance_map = {b.get("acc"): b.get("balanceInEq", "0.00") for b in balances}

        write_privat_transactions_to_sheet(worksheet, transactions, acc_name_map, acc_balance_map)
        update_balances_in_sheet(worksheet, balances)

        today_str = datetime.now().strftime("%d.%m.%Y")
        entry["data"] = today_str
        print(f"📆 Оновлено дату в конфігу на сьогодні: {today_str}")

    config_manager(CONFIG)
