import time
import json
import requests
from datetime import datetime
from config import CONFIG
from table import init_google_sheet


def format_amount(value):
    try:
        return round(float(value), 6)
    except (ValueError, TypeError):
        return 0.0


def export_trc20_transactions_troscan_to_google_sheets():
    erc20_data = CONFIG.get("TRC20", [])
    if not erc20_data:
        print("⚠️ TRC20 адреси у конфігурації не знайдено.")
        return

    worksheet = init_google_sheet()

    all_transactions = []

    for item in erc20_data:
        address = item.get("address")
        if not address:
            continue
        print(f"\n📥 Обробка TRC20 адреси: {address}")
        limit = 50
        start = 0

        while True:
            url = (
                f"https://apilist.tronscanapi.com/api/token_trc20/transfers"
                f"?limit={limit}&start={start}&relatedAddress={address}&confirm=true&filterTokenValue=1"
            )

            response = requests.get(url)
            if response.status_code != 200:
                print(f"❌ Помилка при запиті: статус {response.status_code}")
                break

            data = response.json()
            transactions = data.get("token_transfers", [])

            if not transactions:
                print("✅ Усі TRC20 транзакції отримано.")
                break

            for tx in transactions:
                tx["__wallet_address__"] = address
            all_transactions.extend(transactions)
            print(f"🔄 Отримано {len(transactions)} транзакцій")
            start += limit
            time.sleep(0.4)

    with open("trc20_transactions.json", "w", encoding="utf-8") as f:
        json.dump(all_transactions, f, ensure_ascii=False, indent=2)
    print("💾 Дані збережено у файл trc20_transactions.json")

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
        address = tx.get("__wallet_address__")
        address_lower = address.lower() if address else ""

        timestamp = datetime.fromtimestamp(tx["block_ts"] / 1000).strftime("%d.%m.%Y %H:%M:%S")
        token = tx.get("token_info", {}).get("symbol", "")
        method = "TRC20"
        to_address = tx.get("to_address", "").lower()
        from_address = tx.get("from_address", "").lower()
        tx_hash = tx.get("transaction_id", "")

        try:
            amount = float(tx.get("quant", 0)) / 10 ** int(tx.get("token_info", {}).get("decimals", 6))
        except Exception:
            amount = 0

        fee = 0
        type_operation = "debit" if to_address == address_lower else "credit"
        address_counterparty = to_address if type_operation == "credit" else from_address

        new_row = [""] * 25
        new_row[0] = timestamp
        new_row[1] = method
        new_row[3] = address
        new_row[4] = type_operation
        new_row[5] = abs(format_amount(amount))
        new_row[6] = abs(format_amount(amount))
        new_row[7] = token or "USDT"
        new_row[8] = "" if abs(fee) == 0 else abs(fee)
        new_row[13] = address_counterparty
        new_row[16] = tx_hash

        if tx_hash in existing_tx_by_hash:
            existing = existing_tx_by_hash[tx_hash]
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
