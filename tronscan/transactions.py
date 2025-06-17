import requests
import time
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
def format_amount(value):
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.00
def export_trc20_transactions_troscan_to_google_sheets():
    # ⚙️ Авторизація до Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("api-finanse-de717294db0b.json", scope)
    client = gspread.authorize(creds)

    # 📄 Відкриваємо таблицю
    spreadsheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1Fg9Fo4TLqc0KYbC_GHBRccFZg8a5g9NJPfyMoSLSKM8/edit?usp=sharing"
    )
    worksheet = spreadsheet.worksheet("Аркуш1")

    # 🔗 TRC20 API
    address = "TRoJdqkhtJGpWVsvC67jk4Cp8FDAhQL1LE"
    limit = 50
    start = 0
    all_transactions = []

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

        all_transactions.extend(transactions)
        print(f"🔄 Отримано {len(transactions)} транзакцій")
        start += limit
        time.sleep(0.4)

    # 💾 Зберігаємо у файл
    with open("trc20_transactions.json", "w", encoding="utf-8") as f:
        json.dump(all_transactions, f, ensure_ascii=False, indent=2)
    print("💾 Дані збережено у файл trc20_transactions.json")

    # --- Отримуємо існуючі записи з таблиці ---
    existing_rows = worksheet.get_all_values()
    header_offset = 1  # якщо є заголовок, якщо ні - поставте 0

    # Індекс за tx_hash (колонка Q, індекс 16)
    existing_tx_by_hash = {}
    for i, row in enumerate(existing_rows[header_offset:], start=header_offset + 1):
        full_row = row + [""] * (25 - len(row))
        tx_hash = full_row[16]
        if tx_hash:
            existing_tx_by_hash[tx_hash] = {"row_number": i, "row_data": full_row}

    rows_to_update = []
    rows_to_append = []

    # --- Формуємо дані для запису з перевіркою ---
    address_lower = address.lower()
    for tx in all_transactions:
        timestamp = datetime.fromtimestamp(tx["block_ts"] / 1000).strftime("%Y.%m.%d %H:%M:%S")
        token = tx.get("token_info", {}).get("symbol", "")
        method = "TRC20"
        to_address = tx.get("to_address", "").lower()
        from_address = tx.get("from_address", "").lower()
        tx_hash = tx.get("transaction_id", "")

        try:
            amount = float(tx.get("quant", 0)) / 10 ** int(tx.get("token_info", {}).get("decimals", 6))
        except Exception:
            amount = 0

        fee = 0  # TRC20 не повертає fee
        type_operation = "debit" if to_address == address_lower else "credit"
        address_counterparty = to_address if type_operation == "credit" else from_address

        new_row = [""] * 25
        new_row[0] = timestamp
        new_row[1] = method
        new_row[3] = address
        new_row[4] = type_operation
        amount = abs(format_amount(amount))
        new_row[6] = str(amount).replace('.', ',')
        new_row[7]= "USDT"
        new_row[8] = "" if fee == 0 else fee
        new_row[13] = address_counterparty
        new_row[16] = tx_hash

        if tx_hash in existing_tx_by_hash:
            existing = existing_tx_by_hash[tx_hash]
            if new_row != existing["row_data"]:
                rows_to_update.append((existing["row_number"], new_row))
        else:
            rows_to_append.append(new_row)

    # --- Масове оновлення існуючих рядків ---
    if rows_to_update:
        batch_data = [
            {"range": f"A{row_number}:Y{row_number}", "values": [row_data]}
            for row_number, row_data in rows_to_update
        ]
        worksheet.batch_update(batch_data)
        print(f"🔁 Оновлено {len(rows_to_update)} транзакцій.")

    # --- Масове додавання нових рядків ---
    if rows_to_append:
        start_row = len(existing_rows) + 1
        worksheet.update(f"A{start_row}:Y{start_row + len(rows_to_append) - 1}", rows_to_append)
        print(f"➕ Додано {len(rows_to_append)} нових транзакцій починаючи з рядка {start_row}.")
    else:
        print("✅ Нових транзакцій для додавання немає.")
