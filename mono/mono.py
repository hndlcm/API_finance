import time
import requests
from datetime import datetime, timedelta
from config_manager import CONFIG, config_manager  
from table import init_google_sheet


def format_amount(value):
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.0


def fetch_monobank_transactions(api_key, from_time, to_time, max_retries=5):
    headers = {"X-Token": api_key}
    url = f"https://api.monobank.ua/personal/statement/0/{from_time}/{to_time}"
    retries = 0
    wait_time = 2  # початкова пауза в секундах

    while retries <= max_retries:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print(f"⚠️ Ліміт запитів Mono API перевищено. Очікуємо {wait_time} секунд і пробуємо знову...")
            time.sleep(wait_time)
            retries += 1
            wait_time *= 2  # експоненціальний backoff
        else:
            raise Exception(f"Помилка API Mono: {response.status_code} - {response.text}")

    raise Exception("Превищено максимальну кількість повторів через помилку 429.")


def export_mono_transactions_to_google_sheets():
    mono_entries = CONFIG.get("MONO", [])
    if not mono_entries:
        print("⚠️ MONO гаманці у конфігурації не знайдено.")
        return

    worksheet = init_google_sheet()

    for item in mono_entries:
        api_key = item.get("api_token")
        if not api_key:
            print("⚠️ Відсутній api_token у конфігу Mono.")
            continue

        date_str = item.get("data")
        try:
            config_date = datetime.strptime(date_str, "%d.%m.%Y")
        except Exception:
            print(f"❌ Невірний формат дати в конфігу: {date_str}, використовую сьогоднішню дату")
            config_date = datetime.now()

        from_dt = config_date - timedelta(days=5)
        to_dt = datetime.now()

        print(f"\n📥 Обробка Mono гаманця, період: {from_dt.date()} - {to_dt.date()}")

        all_transactions = []
        chunk_start = from_dt
        chunk_days = 31  # щоб не було перевищень лімітів

        while chunk_start < to_dt:
            chunk_end = min(chunk_start + timedelta(days=chunk_days), to_dt)
            from_time = int(chunk_start.timestamp())
            to_time = int(chunk_end.timestamp())

            print(f"🔄 Завантаження транзакцій з {chunk_start.date()} по {chunk_end.date()}...")

            try:
                txs = fetch_monobank_transactions(api_key, from_time, to_time)
                if not isinstance(txs, list):
                    print(f"❌ Помилка у відповіді Mono API, очікується список транзакцій.")
                    break
                all_transactions.extend(txs)
            except Exception as e:
                print(f"❌ Помилка при отриманні транзакцій Mono: {e}")
                break

            chunk_start = chunk_end + timedelta(seconds=1)
            time.sleep(1.5)  # збільшена пауза, щоб знизити ризик 429

        existing_rows = worksheet.get_all_values()
        header_offset = 1
        existing_tx_by_id = {}
        for i, row in enumerate(existing_rows[header_offset:], start=header_offset + 1):
            full_row = row + [""] * (25 - len(row))
            tx_id = full_row[16]
            if tx_id:
                existing_tx_by_id[tx_id] = {"row_number": i, "row_data": full_row}

        rows_to_update = []
        rows_to_append = []

        for tx in all_transactions:
            tx_id = str(tx.get("id", ""))
            if not tx_id:
                continue

            dt = datetime.fromtimestamp(tx.get("time", 0))
            timestamp = dt.strftime("%d.%m.%Y %H:%M:%S")
            amount = abs(format_amount(tx.get("amount", 0)) / 100)
            balance = abs(format_amount(tx.get("balance", 0)) / 100)
            description = tx.get("description", "")
            type_op = "debit" if tx.get("amount", 0) < 0 else "credit"

            new_row = [""] * 25
            new_row[0] = timestamp
            new_row[1] = "Mono"
            new_row[4] = type_op
            new_row[5] = amount
            new_row[6] = amount
            new_row[7] = "UAH"
            new_row[10] = description
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
            print(f"➕ Додано {len(rows_to_append)} нових транзакцій з рядка {start_row}.")
        else:
            print("✅ Нових транзакцій для додавання немає.")
        
        today_str = datetime.now().strftime("%d.%m.%Y")
        item["data"] = today_str
        print(f"📆 Оновлено дату в конфігу на сьогодні: {today_str}")

        # Записуємо оновлений конфіг назад у файл
        config_manager(CONFIG)

