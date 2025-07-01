import requests
import time
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import CONFIG


def format_amount(value):
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.00


def export_erc20_to_google_sheet():
    # Авторизація Google Sheets
    sheet_conf = CONFIG["google_sheet"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(sheet_conf["credentials_path"], scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(sheet_conf["spreadsheet_url"])
    worksheet = spreadsheet.worksheet(sheet_conf["worksheet_name"])

    erc20_entries = CONFIG.get("ERC20", [])
    if not erc20_entries:
        print("⚠️ Немає налаштованих ERC20 акаунтів у конфігурації.")
        return

    existing_rows = worksheet.get_all_values()
    header_offset = 1
    existing_tx_by_hash = {}
    for i, row in enumerate(existing_rows[header_offset:], start=header_offset + 1):
        full_row = row + [""] * (25 - len(row))
        tx_hash = full_row[16]
        if tx_hash:
            existing_tx_by_hash[tx_hash] = {"row_number": i, "row_data": full_row}

    for entry in erc20_entries:
        address = entry["address"]
        api_key = entry["api_key"]
        date_str = entry.get("data")

        # Визначаємо дату з конфігу
        if not date_str:
            config_date = datetime.now().date()
        else:
            try:
                config_date = datetime.strptime(date_str, "%d.%m.%Y").date()
            except Exception:
                print(f"❌ Невірний формат дати в конфігу: {date_str}, використовуємо сьогоднішню дату")
                config_date = datetime.now().date()

        # Віднімаємо 5 днів для початку інтервалу
        from_date = config_date - timedelta(days=5)
        to_date = config_date

        print(f"\n🔍 Обробка адреси {address} ({entry.get('name', '')}), діапазон дат: {from_date} - {to_date}")

        page = 1
        all_transactions = []

        while True:
            url = (
                f"https://api.etherscan.io/api"
                f"?module=account&action=tokentx&address={address}"
                f"&startblock=0&endblock=99999999&page={page}&offset=100&sort=asc"
                f"&apikey={api_key}"
            )
            response = requests.get(url)
            if response.status_code != 200:
                print("❌ Помилка при запиті:", response.status_code)
                break
            result = response.json()
            transactions = result.get("result", [])
            if not transactions:
                break

            # Фільтруємо транзакції по даті (timestamp у секундах)
            filtered_transactions = []
            for tx in transactions:
                ts = int(tx.get("timeStamp", 0))
                tx_date = datetime.utcfromtimestamp(ts).date()
                if from_date <= tx_date <= to_date:
                    filtered_transactions.append(tx)
                elif tx_date > to_date:
                    # Оскільки вони відсортовані, якщо дата більша за to_date — можна припинити обробку сторінок
                    break

            all_transactions.extend(filtered_transactions)
            print(f"🔄 Сторінка {page}: Отримано {len(filtered_transactions)} транзакцій (всього: {len(all_transactions)})")

            # Якщо на сторінці менше 100 транзакцій або дата в наступних не підходить — виходимо
            if len(transactions) < 100 or any(datetime.utcfromtimestamp(int(tx.get("timeStamp",0))).date() > to_date for tx in transactions):
                break

            page += 1
            time.sleep(0.3)

        rows_to_update = []
        rows_to_append = []

        for tx in all_transactions:
            timestamp = datetime.fromtimestamp(int(tx["timeStamp"])).strftime("%d.%m.%Y %H:%M:%S")
            token_symbol = tx.get("tokenSymbol", "UNKNOWN")
            token_decimal = int(tx.get("tokenDecimal", "6"))
            from_address, to_address = tx.get("from", ""), tx.get("to", "")
            tx_hash = tx.get("hash", "")
            try:
                amount = int(tx.get("value", "0")) / (10 ** token_decimal)
            except Exception:
                amount = 0

            type_operation = "debit" if to_address.lower() == address.lower() else "credit"
            counterparty = to_address if type_operation == "credit" else from_address
            formatted_amount = abs(format_amount(amount))

            row = [""] * 25
            row[0] = timestamp
            row[1] = "ERC20"
            row[3] = address
            row[4] = type_operation
            row[5] = formatted_amount
            row[6] = formatted_amount
            row[7] = token_symbol
            row[13] = counterparty
            row[16] = tx_hash

            if tx_hash in existing_tx_by_hash:
                existing = existing_tx_by_hash[tx_hash]
                if row != existing["row_data"]:
                    rows_to_update.append((existing["row_number"], row))
            else:
                rows_to_append.append(row)

        # Оновлення рядків
        if rows_to_update:
            batch_data = [{"range": f"A{row_number}:Y{row_number}", "values": [row_data]} for row_number, row_data in rows_to_update]
            worksheet.batch_update(batch_data)
            print(f"🔁 Оновлено {len(rows_to_update)} транзакцій.")

        # Додавання нових
        if rows_to_append:
            start_row = len(existing_rows) + 1
            worksheet.update(f"A{start_row}:Y{start_row + len(rows_to_append) - 1}", rows_to_append)
            print(f"➕ Додано {len(rows_to_append)} нових транзакцій з рядка {start_row}.")
        else:
            print("✅ Нових транзакцій для додавання немає.")

        # Оновлення дати в конфігу на сьогодні
        today_str = datetime.now().strftime("%d.%m.%Y")
        entry["data"] = today_str
        print(f"📆 Оновлено дату в конфігу на сьогодні: {today_str}")

