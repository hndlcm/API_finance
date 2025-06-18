import requests
import time
import json
import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def format_amount(value):
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.00

def format_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y.%m.%d %H:%M:%S")
    except Exception:
        return date_str

def export_erc20_to_google_sheet():
    # --- Авторизація Google Sheets ---
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("api-finanse-de717294db0b.json", scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Fg9Fo4TLqc0KYbC_GHBRccFZg8a5g9NJPfyMoSLSKM8/edit?usp=sharing")
    worksheet = spreadsheet.worksheet("Аркуш1")

    # --- Параметри Etherscan ---
    load_dotenv()
    api_key = os.getenv("ETHER")
    address = "0x19Cf249E7e423b5Bd2d41FD62e7f3adbfdEe5B47"
    start_block, end_block, page, offset = 0, 99999999, 1, 100
    all_transactions = []

    while True:
        url = (
            f"https://api.etherscan.io/api"
            f"?module=account&action=tokentx&address={address}"
            f"&startblock={start_block}&endblock={end_block}&page={page}&offset={offset}&sort=asc"
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

    with open("erc20_transactions.json", "w", encoding="utf-8") as f:
        json.dump(all_transactions, f, ensure_ascii=False, indent=4)

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
            fee = (gas_used * gas_price) / 10**18
        except Exception:
            fee = 0

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

    # --- Оновлення рядків ---
    if rows_to_update:
        batch_data = [{"range": f"A{row_number}:Y{row_number}", "values": [row_data]} for row_number, row_data in rows_to_update]
        worksheet.batch_update(batch_data)
        print(f"🔁 Оновлено {len(rows_to_update)} транзакцій.")

    # --- Додавання нових ---
    if rows_to_append:
        start_row = len(existing_rows) + 1
        worksheet.update(f"A{start_row}:Y{start_row + len(rows_to_append) - 1}", rows_to_append)
        print(f"➕ Додано {len(rows_to_append)} нових транзакцій з рядка {start_row}.")
    else:
        print("✅ Нових транзакцій для додавання немає.")
