import time
from datetime import datetime, timedelta

import requests

from config_manager import CURRENCY_CODES, config_manager
from table import init_google_sheet
from utils import (
    datetime_to_serial_float,
    format_amount,
    get_mono_exchange_rates,
)

BASE_URL_TRANSACTIONS = "https://acp.privatbank.ua/api/statements/transactions"
BASE_URL_BALANCES = "https://acp.privatbank.ua/api/statements/balance/final"


def fetch_transactions(
    api_token, start_date: str, end_date: str, limit: int = 100
) -> list:
    headers = {
        "User-Agent": "MyApp/1.0",
        "token": api_token,
        "Content-Type": "application/json;charset=cp1251",
    }
    params = {"startDate": start_date, "endDate": end_date, "limit": limit}
    all_transactions = []

    while True:
        response = requests.get(
            BASE_URL_TRANSACTIONS, headers=headers, params=params
        )
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
        "Content-Type": "application/json;charset=cp1251",
    }
    params = {"limit": 100}
    all_balances = []

    while True:
        response = requests.get(
            BASE_URL_BALANCES, headers=headers, params=params
        )
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


def write_privat_transactions_to_sheet(
    worksheet, transactions: list, acc_name_map: dict, exchange_rates
):
    try:
        existing_rows = worksheet.get_all_values()
    except Exception:
        print("⚠️ Зачекай 60 секунд (Rate Limit)...")
        time.sleep(60)
        existing_rows = worksheet.get_all_values()

    header_offset = 1
    existing_tx_by_id = {}
    for i, row in enumerate(
        existing_rows[header_offset:], start=header_offset + 1
    ):
        if len(row) > 16 and row[16]:
            existing_tx_by_id[row[16]] = {
                "row_number": i,
                "row_data": row + [""] * (25 - len(row)),
            }

    rows_to_update = []
    rows_to_append = []

    for tx in transactions:
        new_row = [""] * 25

        datetime_str = f"{tx.get('DAT_KL', '')} {tx.get('TIM_P', '')}"
        try:
            tx_time = datetime.strptime(datetime_str, "%d.%m.%Y %H:%M")
            new_row[0] = datetime_to_serial_float(tx_time)
        except Exception:
            new_row[0] = datetime_str.strip()

        account = tx.get("AUT_MY_ACC", "")
        account_currency = tx.get("CCY", "UAH")
        #operation_currency = tx.get("CCY_E", account_currency)

        new_row[1] = "privatbank"
        new_row[2] = acc_name_map.get(account, "")
        new_row[3] = account
        new_row[4] = "debit" if tx.get("TRANTYPE") == "D" else "credit"
        amount_operation = format_amount(tx.get("SUM", "0").replace(",", "."))
        new_row[5] = format_amount(tx.get("SUM_E", "0").replace(",", "."))
        new_row[6] = amount_operation  # у валюті операції

        new_row[7] = CURRENCY_CODES.get(account_currency, account_currency)
        new_row[10] = tx.get("OSND", "")
        new_row[11] = tx.get("AUT_CNTR_NAM", "")
        try:
            new_row[12] = int(tx.get("AUT_CNTR_CRF", "0"))
        except Exception:
            new_row[12] = 0
        new_row[13] = tx.get("AUT_CNTR_ACC", "")
        new_row[16] = tx.get("ID", "")

        tx_id = new_row[16]
        if tx_id in existing_tx_by_id:
            existing = existing_tx_by_id[tx_id]
            if not new_row[9] and len(existing["row_data"]) > 9:
                new_row[9] = existing["row_data"][9]
            if new_row != existing["row_data"]:
                rows_to_update.append((existing["row_number"], new_row))
        else:
            rows_to_append.append(new_row)

    if rows_to_update:
        batch_data = [
            {"range": f"A{row_number}:Y{row_number}", "values": [row_data]}
            for row_number, row_data in rows_to_update
        ]
        worksheet.batch_update(batch_data, value_input_option="USER_ENTERED")
        print(f"🔁 Оновлено {len(rows_to_update)} транзакцій.")

    if rows_to_append:
        start_row = len(existing_rows) + 1
        worksheet.update(
            f"A{start_row}:Y{start_row + len(rows_to_append) - 1}",
            rows_to_append,
            value_input_option="USER_ENTERED",
        )
        print(
            f"➕ Додано {len(rows_to_append)} нових транзакцій починаючи з рядка {start_row}."
        )
    else:
        print("✅ Нових транзакцій немає.")


def privat_export():
    CONFIG = config_manager()
    tokens = CONFIG.get("PRIVAT", [])

    if not tokens:
        print("❌ У конфігурації немає PRIVAT токенів.")
        return

    worksheet = init_google_sheet()
    exchange_rates = get_mono_exchange_rates()

    for entry in tokens:
        api_token = entry.get("api_token")
        days = entry.get("days", 5)

        if not api_token:
            print("⚠️ Пропущено через відсутність токена")
            continue

        to_date_dt = datetime.now()
        from_date_dt = to_date_dt - timedelta(days=days)

        from_date = from_date_dt.strftime("%d-%m-%Y")
        to_date = to_date_dt.strftime("%d-%m-%Y")

        print(
            f"\n📆 Обробка транзакцій за останні {days} днів: з {from_date} до {to_date}"
        )

        transactions = fetch_transactions(api_token, from_date, to_date)

        print("📈 Отримання фінальних балансів...")
        balances = fetch_balances(api_token)

        acc_name_map = {b.get("acc"): b.get("nameACC") for b in balances}

        write_privat_transactions_to_sheet(
            worksheet, transactions, acc_name_map, exchange_rates
        )
