import time
import requests
from datetime import datetime, timedelta
from pytz import timezone
from gspread.utils import rowcol_to_a1
from table import init_google_sheet
from config_manager import CONFIG, config_manager

BASE_URL_BALANCES = "https://acp.privatbank.ua/api/statements/balance/final"


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


def update_balances_in_sheet(worksheet, acc_balance_map: dict):
    print("\n📊 Оновлення балансів у таблиці...")
    existing_rows = worksheet.get_all_values()

    col_type = 2     # колонка B
    col_account = 4  # колонка D
    col_balance = 10 # колонка J

    batch_data = []

    for i, row in enumerate(existing_rows, start=1):
        if len(row) >= col_type and row[col_type - 1].strip().lower() == "privatbank":
            if len(row) >= col_account:
                account = row[col_account - 1].strip()
                balance = acc_balance_map.get(account)
                if balance is not None:
                    cell_range = rowcol_to_a1(i, col_balance)
                    batch_data.append({
                        "range": cell_range,
                        "values": [[balance]]
                    })
                    print(f"🔄 Оновлюємо баланс для {account}: {balance} → {cell_range}")

    if batch_data:
        worksheet.batch_update(batch_data)
        print(f"✅ Успішно оновлено {len(batch_data)} балансів.")
    else:
        print("⚠️ Не знайдено записів для оновлення.")


def append_balance_rows_to_sheet(worksheet, balances: list):
    now = datetime.now(timezone("Europe/Kyiv")).strftime("%d.%m.%y %H:%M")
    new_rows = []

    for b in balances:
        row = [""] * 25
        row[0] = now                                # Дата
        row[1] = "privatbank"                       # Джерело
        row[2] = b.get("nameACC", "")               # Назва рахунку
        row[3] = b.get("acc", "")                   # IBAN
        row[4] = "balance"                          # Тип операції
        try:
            balance = float(str(b.get("balanceOutEq", "0")).replace(",", "."))
        except Exception:
            balance = 0.0
        row[5] = balance                            # debit
        row[6] = balance                            # credit
        row[7] = b.get("ccy", "UAH")                # Валюта

        new_rows.append(row)

    if new_rows:
        worksheet.append_rows(new_rows, value_input_option="USER_ENTERED")
        print(f"➕ Додано {len(new_rows)} рядків типу 'balance'")
    else:
        print("⚠️ Немає нових балансів для додавання.")


def run_balance_update():
    tokens = CONFIG.get("PRIVAT", [])
    if not tokens:
        print("❌ У конфігурації немає токенів PRIVAT.")
        return

    worksheet = init_google_sheet()
    acc_balance_map = {}

    rows = worksheet.get_all_values()
    accounts = set()
    for row in rows:
        if len(row) >= 4 and row[1].strip().lower() == "privatbank":
            accounts.add(row[3].strip())

    for entry in tokens:
        api_token = entry.get("api_token")
        if not api_token:
            continue

        # Отримуємо всі баланси з токена
        balances = fetch_balances(api_token)

        # Додаємо окремі рядки з балансами
        append_balance_rows_to_sheet(worksheet, balances)

        # Будуємо мапу для оновлення в існуючих рядках
        for acc in accounts:
            if acc and acc not in acc_balance_map:
                balance_obj = next((b for b in balances if b.get("acc") == acc), None)
                if balance_obj:
                    acc_balance_map[acc] = balance_obj.get("balanceOutEq", "0.00")
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
        print(f"🕔 Очікуємо до {next_run.strftime('%Y-%m-%d %H:%M:%S')} (Kyiv)...")
        time.sleep(wait_seconds)
        run_balance_update()


if __name__ == "__main__":
    wait_until_5am_kyiv()
