import requests
import time
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config_manager import config_manager

def format_amount(value):
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.00
    

def timestamp_to_serial_date(ts: int):
    try:
        dt = datetime.fromtimestamp(ts)
        epoch = datetime(1899, 12, 30)
        delta = dt - epoch
        return delta.days + (delta.seconds + delta.microseconds / 1e6) / 86400
    except Exception:
        return ""


def export_erc20_to_google_sheet():
    CONFIG = config_manager() 
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
        days = entry.get("days", 5)

        from_date = datetime.now().date() - timedelta(days=days)
        to_date = datetime.now().date()

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

            filtered_transactions = []
            for tx in transactions:
                ts = int(tx.get("timeStamp", 0))
                tx_date = datetime.utcfromtimestamp(ts).date()
                if from_date <= tx_date <= to_date:
                    filtered_transactions.append(tx)
                elif tx_date > to_date:
                    break

            all_transactions.extend(filtered_transactions)
            print(f"🔄 Сторінка {page}: Отримано {len(filtered_transactions)} транзакцій (всього: {len(all_transactions)})")

            if len(transactions) < 100 or any(datetime.utcfromtimestamp(int(tx.get("timeStamp", 0))).date() > to_date for tx in transactions):
                break

            page += 1
            time.sleep(0.3)

        rows_to_update = []
        rows_to_append = []

        for tx in all_transactions:
            ts = int(tx["timeStamp"])
            serial_date = timestamp_to_serial_date(ts)
            token_symbol = tx.get("tokenSymbol", "UNKNOWN")
            token_decimal = int(tx.get("tokenDecimal", "6"))
            from_address, to_address = tx.get("from", ""), tx.get("to", "")
            tx_hash = tx.get("hash", "")
            try:
                amount = int(tx.get("value", "0")) / (10 ** token_decimal)
            except Exception:
                amount = 0

            type_operation = "debit" if to_address == address else "credit"
            counterparty = to_address if type_operation == "credit" else from_address
            formatted_amount = abs(format_amount(amount))

            row = [""] * 25
            row[0] = serial_date
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
            end_row = start_row + len(rows_to_append) - 1

            current_max_rows = worksheet.row_count
            if end_row > current_max_rows:
                rows_to_add = end_row - current_max_rows
                worksheet.add_rows(rows_to_add)
                print(f"➕ Додано {rows_to_add} нових рядків до аркуша.")

            worksheet.update(f"A{start_row}:Y{end_row}", rows_to_append)
            print(f"✅ Додано {len(rows_to_append)} нових транзакцій з рядка {start_row}.")
        else:
            print("✅ Нових транзакцій для додавання немає.")
