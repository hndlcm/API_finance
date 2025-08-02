import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from config_manager import config_manager
from table import init_google_sheet

BASE_URL_BALANCES = "https://acp.privatbank.ua/api/statements/balance/final"


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


def convert_to_serial_date(dt: datetime) -> float:
    """Конвертує datetime до числа формату Google Sheets (serial date)"""
    epoch = datetime(1899, 12, 30, tzinfo=dt.tzinfo)
    delta = dt - epoch
    return delta.days + (delta.seconds + delta.microseconds / 1e6) / 86400


def append_balance_rows_to_sheet(
    worksheet, balances: list, current_dt: datetime
):
    current_serial = convert_to_serial_date(current_dt)
    new_rows = []

    for b in balances:
        row = [""] * 25
        row[0] = current_serial
        row[1] = "privatbank"
        row[2] = b.get("nameACC", "")
        row[3] = b.get("acc", "")
        row[4] = "balance"
        try:
            balance = float(str(b.get("balanceOutEq", "0")).replace(",", "."))
        except Exception:
            balance = 0.0
        row[7] = b.get("currency", "UAH")
        row[9] = balance

        new_rows.append(row)

    if new_rows:
        worksheet.append_rows(new_rows, value_input_option="USER_ENTERED")
        print(f"➕ Додано {len(new_rows)} рядків типу 'balance'")
    else:
        print("⚠️ Немає нових балансів для додавання.")


def run_balance_update():
    CONFIG = config_manager()
    tokens = CONFIG.get("PRIVAT", [])
    if not tokens:
        print("❌ У конфігурації немає токенів PRIVAT.")
        return

    worksheet = init_google_sheet()
    current_dt = datetime.now(ZoneInfo("Europe/Kyiv"))

    for entry in tokens:
        api_token = entry.get("api_token")
        if not api_token:
            continue

        balances = fetch_balances(api_token)
        append_balance_rows_to_sheet(worksheet, balances, current_dt)


def wait_until_5am_kyiv():
    kyiv = ZoneInfo("Europe/Kyiv")
    while True:
        now = datetime.now(kyiv)
        next_run = now.replace(hour=5, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)
        wait_seconds = (next_run - now).total_seconds()
        print(
            f"🕔 Очікуємо до {next_run.strftime('%Y-%m-%d %H:%M:%S')} (Kyiv)..."
        )
        time.sleep(wait_seconds)
        run_balance_update()


if __name__ == "__main__":
    wait_until_5am_kyiv()
