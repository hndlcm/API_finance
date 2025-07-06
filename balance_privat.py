import time
import requests
from datetime import datetime, timedelta
from pytz import timezone
from gspread.utils import rowcol_to_a1  # Додано для правильного формування A1-адреси
from table import init_google_sheet
from config_manager import CONFIG

BASE_URL_BALANCES = "https://acp.privatbank.ua/api/statements/balance/final"

def fetch_balances(api_token: str, account: str) -> list:
    headers = {
        "User-Agent": "MyApp/1.0",
        "token": api_token,
        "Content-Type": "application/json;charset=cp1251"
    }
    params = {"acc": account}
    try:
        response = requests.get(BASE_URL_BALANCES, headers=headers, params=params)
        if response.status_code != 200:
            print(f"❌ Помилка {response.status_code} для рахунку {account}")
            return []
        data = response.json()
        return data.get("balances", [])
    except Exception as e:
        print(f"❌ Виняток при запиті балансу: {e}")
        return []

def update_balances_in_sheet(worksheet, acc_balance_map: dict):
    print("\n📊 Оновлення балансів у таблиці...")
    existing_rows = worksheet.get_all_values()

    col_type = 2     # колонка B (1-based)
    col_account = 4  # колонка D
    col_balance = 10 # колонка J

    rows_to_update = []

    for i, row in enumerate(existing_rows, start=1):  # start=1 бо Google Sheets починає з 1
        if len(row) >= col_type and row[col_type - 1].strip().lower() == "privatbank":
            if len(row) >= col_account:
                account = row[col_account - 1].strip()
                balance = acc_balance_map.get(account)
                if balance is not None:
                    cell_range = rowcol_to_a1(i, col_balance)
                    rows_to_update.append({
                        "range": cell_range,
                        "values": [[balance]]
                    })
                    print(f"🔄 Оновлено баланс для {account}: {balance} → {cell_range}")

    if rows_to_update:
        for update in rows_to_update:
            worksheet.update(update["range"], update["values"])
        print(f"✅ Успішно оновлено {len(rows_to_update)} балансів.")
    else:
        print("⚠️ Не знайдено записів для оновлення.")

def run_balance_update():
    tokens = CONFIG.get("PRIVAT", [])
    if not tokens:
        print("❌ У конфігурації немає токенів.")
        return

    worksheet = init_google_sheet()
    acc_balance_map = {}

    for entry in tokens:
        api_token = entry.get("api_token")
        if not api_token:
            continue

        rows = worksheet.get_all_values()
        for row in rows:
            if len(row) >= 4 and row[1].strip().lower() == "privatbank":
                acc = row[3].strip()
                if acc and acc not in acc_balance_map:
                    balances = fetch_balances(api_token, acc)
                    if balances:
                        acc_balance_map[acc] = balances[0].get("balanceOutEq", "0.00")
                    else:
                        acc_balance_map[acc] = "0.00"

    update_balances_in_sheet(worksheet, acc_balance_map)

def wait_until_5am_kyiv():
    kyiv = timezone("Europe/Kyiv")
    while True:
        now = datetime.now(kyiv)
        next_run = now.replace(hour=5, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)
        wait_seconds = (next_run - now).total_seconds()
        print(f"🕔 Очікування до {next_run.strftime('%Y-%m-%d %H:%M:%S')} (Kyiv)...")
        time.sleep(wait_seconds)
        run_balance_update()

if __name__ == "__main__":
    wait_until_5am_kyiv()
