import requests
import time
import json
import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from config import CONFIG

def load_wallets(file_path="wallets.txt"):
    wallets = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue
            system, data = line.split("=", 1)
            system = system.strip()
            entries = [x.strip() for x in data.split(";") if x.strip()]
            wallets[system] = []
            for entry in entries:
                # Кожен запис у вигляді "address,apikey"
                parts = [x.strip() for x in entry.split(",")]
                if len(parts) == 2:
                    wallets[system].append({"address": parts[0], "apikey": parts[1]})
                else:
                    print(f"⚠️ Помилка формату для {system}: {entry}")
    return wallets


def format_amount(value):
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.00


def export_erc20_to_google_sheet():
    # --- Авторизація Google Sheets ---
    sheet_conf = CONFIG["google_sheet"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(sheet_conf["credentials_path"], scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(sheet_conf["spreadsheet_url"])
    worksheet = spreadsheet.worksheet(sheet_conf["worksheet_name"])

    erc20_data = CONFIG.get("ERC20", [])

    existing_rows = worksheet.get_all_values()
    header_offset = 1
    existing_tx_by_hash = {}
    for i, row in enumerate(existing_rows[header_offset:], start=header_offset + 1):
        full_row = row + [""] * (25 - len(row))
        tx_hash = full_row[16]
        if tx_hash:
            existing_tx_by_hash[tx_hash] = {"row_number": i, "row_data": full_row}

    rows_to_update = []
    rows_to_append = []

    for entry in erc20_data:
        address = entry["address"]
        api_key = entry["api_key"]
        page = 1
        all_transactions = []

        print(f"\n🔍 Обробка адреси {address} ({entry.get('name', '')})")

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
            all_transactions.extend(transactions)
            print(f"🔄 Сторінка {page}: {len(transactions)} транзакцій (всього: {len(all_transactions)})")
            page += 1
            time.sleep(0.3)

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
            try:
                gas_used = int(tx.get("gasUsed", "0"))
                gas_price = int(tx.get("gasPrice", "0"))
                fee = (gas_used * gas_price) / 10 ** 18
            except Exception:
                fee = 0

            type_operation = "debit" if to_address.lower() == address.lower() else "credit"
            counterparty = to_address if type_operation == "credit" else from_address
            formatted_amount = abs(format_amount(amount))

            row = [""] * 25
            row[0] = timestamp
            row[1] = "ERC20"
            row[2] = entry.get("name", "")
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

    # --- Оновлення рядків ---
    if rows_to_update:
        batch_data = [{"range": f"A{row_number}:Y{row_number}", "values": [row_data]} for row_number, row_data in
                      rows_to_update]
        worksheet.batch_update(batch_data)
        print(f"🔁 Оновлено {len(rows_to_update)} транзакцій.")

    # --- Додавання нових ---
    if rows_to_append:
        start_row = len(existing_rows) + 1
        worksheet.update(f"A{start_row}:Y{start_row + len(rows_to_append) - 1}", rows_to_append)
        print(f"➕ Додано {len(rows_to_append)} нових транзакцій з рядка {start_row}.")
    else:
        print("✅ Нових транзакцій для додавання немає.")


