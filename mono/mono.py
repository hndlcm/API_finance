import time
import requests
from datetime import datetime, timedelta
from config_manager import config_manager, CURRENCY_CODES
from table import init_google_sheet
from utils import datetime_to_serial_float, format_amount, get_mono_exchange_rates, convert_currency



def convert_to_serial_date(dt: datetime) -> float:
    epoch = datetime(1899, 12, 30)
    delta = dt - epoch
    return delta.days + (delta.seconds + delta.microseconds / 1e6) / 86400


def fetch_monobank_transactions(account_id, api_key, from_time, to_time, max_retries=5):
    headers = {"X-Token": api_key}
    url = f"https://api.monobank.ua/personal/statement/{account_id}/{from_time}/{to_time}"
    retries = 0
    wait_time = 2

    while retries <= max_retries:
        time.sleep(66)
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print(f"⚠️ Ліміт запитів Mono API перевищено. Очікуємо {wait_time} секунд...")
            time.sleep(wait_time)
            retries += 1
            wait_time *= 2
        else:
            raise Exception(f"❌ Помилка API Mono: {response.status_code} - {response.text}")
    raise Exception("❌ Перевищено кількість повторів через помилку 429.")


def get_monobank_accounts(api_key):
    headers = {"X-Token": api_key}
    url = "https://api.monobank.ua/personal/client-info"
    time.sleep(1)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        name = data.get("name", "unknown")
        accounts = data.get("accounts", [])
        account_map = {}
        for acc in accounts:
            account_map[acc["id"]] = {
                "iban": acc.get("iban", f"Mono-{acc['id']}"),
                "account_currency": acc.get("currencyCode")
            }
        return name, account_map
    print(f"❌ Помилка отримання account-info: {response.status_code} - {response.text}")
    return "unknown", {}



def export_mono_transactions_to_google_sheets():
    CONFIG = config_manager()
    mono_entries = CONFIG.get("MONO", [])
    if not mono_entries:
        print("⚠️ MONO гаманці у конфігу не знайдено.")
        return

    worksheet = init_google_sheet()
    rates = get_mono_exchange_rates()

    for item in mono_entries:
        api_key = item.get("api_token")
        if not api_key:
            print("⚠️ Відсутній api_token у MONO конфігу.")
            continue

        days = item.get("days", 5)
        to_dt = datetime.now()
        from_dt = to_dt - timedelta(days=days)

        client_name, accounts = get_monobank_accounts(api_key)
        if not accounts:
            print("❌ Не знайдено рахунків для токена.")
            continue

        for account_id, account_info in accounts.items():
            iban = account_info.get("iban", f"Mono-{account_id}")
            print(f"\n📥 Рахунок: {iban}, період: {from_dt.date()} - {to_dt.date()}")

            all_transactions = []
            chunk_start = from_dt
            chunk_days = 31

            while chunk_start < to_dt:
                chunk_end = min(chunk_start + timedelta(days=chunk_days), to_dt)
                from_time = int(chunk_start.timestamp())
                to_time = int(chunk_end.timestamp())

                print(f"🔄 Транзакції з {chunk_start.date()} по {chunk_end.date()}")

                try:
                    txs = fetch_monobank_transactions(account_id, api_key, from_time, to_time)
                    if not isinstance(txs, list):
                        print("❌ Очікував список транзакцій.")
                        break
                    all_transactions.extend(txs)
                except Exception as e:
                    print(f"❌ Помилка при отриманні транзакцій: {e}")
                    break

                chunk_start = chunk_end + timedelta(seconds=1)

            existing_rows = worksheet.get_all_values()
            header_offset = 1
            existing_tx_by_id = {}
            for i, row in enumerate(existing_rows[header_offset:], start=header_offset + 1):
                full_row = row + [""] * (25 - len(row))
                tx_id = full_row[16]
                if tx_id:
                    existing_tx_by_id[str(tx_id)] = {"row_number": i, "row_data": full_row}

            rows_to_update = []
            rows_to_append = []

            for tx in all_transactions:
                tx_id = str(tx.get("id", ""))
                if not tx_id:
                    continue

                dt = datetime.fromtimestamp(tx.get("time", 0))
                timestamp = convert_to_serial_date(dt)

                balance = abs(format_amount(tx.get("balance", 0)) / 100)
                type_op = "debit" if tx.get("amount", 0) < 0 else "credit"

                account_currency = account_info.get("account_currency")
                operation_currency = tx.get("operationCurrencyCode", account_currency)
                
                operation_amount = abs(format_amount(tx.get("operationAmount", tx.get("amount", 0))) / 100)
                converted_amount = convert_currency(operation_amount, operation_currency, account_currency, rates)

                new_row = [""] * 25
                new_row[0] = timestamp
                new_row[1] = "monobank"
                new_row[2] = client_name
                new_row[3] = iban
                new_row[4] = type_op
                new_row[5] = converted_amount  # валюта рахунку
                new_row[6] = operation_amount  # валюта операції
                new_row[7] = CURRENCY_CODES.get(operation_currency, operation_currency)
                new_row[8] = abs(format_amount(tx.get("commissionRate", 0)) / 100)  # комісія
                new_row[9] = balance
                new_row[10] = tx.get("comment", "")
                new_row[11] = tx.get("counterName", "")
                new_row[12] = tx.get("counterEdrpou", 0) if tx.get("counterEdrpou") else ""
                new_row[13] = tx.get("counterIban", "")
                new_row[14] = tx.get("mcc", "")
                new_row[15] = tx.get("description", "")
                new_row[16] = tx_id

                if tx_id in existing_tx_by_id:
                    existing = existing_tx_by_id[tx_id]
                    if new_row != existing["row_data"]:
                        rows_to_update.append((existing["row_number"], new_row))
                else:
                    rows_to_append.append(new_row)

            if rows_to_update:
                batch_data = [{"range": f"A{row_number}:Y{row_number}", "values": [row_data]}
                              for row_number, row_data in rows_to_update]
                worksheet.batch_update(batch_data)
                print(f"🔁 Оновлено {len(rows_to_update)} транзакцій.")

            if rows_to_append:
                start_row = len(existing_rows) + 1
                worksheet.update(f"A{start_row}:Y{start_row + len(rows_to_append) - 1}", rows_to_append)
                print(f"➕ Додано {len(rows_to_append)} нових транзакцій.")
            else:
                print("✅ Нових транзакцій немає.")

