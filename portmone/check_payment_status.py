import requests
import time
import json
from datetime import datetime, timedelta
from table import init_google_sheet
from config_manager import config_manager


def format_amount(value):
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.00


def datetime_to_serial_float(dt: datetime) -> float:
    epoch = datetime(1899, 12, 30)
    return (dt - epoch).total_seconds() / 86400


def get_all_payment_statuses(start_date: str, end_date: str):
    CONFIG = config_manager()
    portmone_config = CONFIG.get("PORTMONE", [{}])[0]

    PORTMONE_URL = "https://www.portmone.com.ua/gateway/"
    PAYEE_ID = portmone_config.get("payee_id")
    LOGIN = portmone_config.get("login")
    PASSWORD = portmone_config.get("password")

    if not (PAYEE_ID and LOGIN and PASSWORD):
        print("❌ В конфігурації не задані дані Portmone (login, password, payee_id)")
        return []

    payload = {
        "method": "result",
        "params": {
            "data": {
                "login": LOGIN,
                "password": PASSWORD,
                "payeeId": PAYEE_ID,
                "id": "123",
                "startDate": start_date,
                "endDate": end_date
            }
        }
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(PORTMONE_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and "result" in data:
            if isinstance(data["result"], dict) and "orders" in data["result"]:
                return data["result"]["orders"]
            elif isinstance(data["result"], list):
                return data["result"]
            else:
                print("❗️ Неочікуваний формат 'result' у відповіді Portmone")
                return []
        elif isinstance(data, list):
            return data
        else:
            return []

    except requests.exceptions.RequestException as e:
        print(f"❌ Помилка запиту Portmone: {e}")
        return []


def write_orders_to_sheet(worksheet, orders: list):
    try:
        existing_rows = worksheet.get_all_values()
    except Exception:
        print("⚠️ Зачекай 60 секунд (Rate Limit)...")
        time.sleep(60)
        existing_rows = worksheet.get_all_values()

    header_offset = 1
    existing_orders_by_id = {}
    for i, row in enumerate(existing_rows[header_offset:], start=header_offset + 1):
        if len(row) > 16 and row[16]:
            existing_orders_by_id[row[16]] = {"row_number": i, "row_data": row + [""] * (25 - len(row))}

    rows_to_update = []
    rows_to_append = []

    for order in orders:
        new_row = [""] * 25
        date_str = order.get("pay_date", "")
        try:
            dt = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
            new_row[0] = datetime_to_serial_float(dt)
        except Exception:
            new_row[0] = date_str
        new_row[1] = "portmone"
        new_row[2] = order.get("payee_name", "")
        status = order.get("status", "")
        new_row[4] = "debit" if status == "PAYED" else "invoice" if status == "CREATED" else status
        amount = abs(format_amount(order.get("billAmount")))
        new_row[5] = amount
        new_row[6] = amount
        new_row[7] = "UAH"
        new_row[8] = abs(format_amount(order.get("payee_commission")))
        new_row[10] = order.get("description", "")
        new_row[11] = f'{order.get("cardBankName", "")}, {order.get("cardTypeName", "")}, {order.get("gateType", "")}'
        new_row[13] = order.get("cardMask", "")
        new_row[15] = f'{order.get("errorCode", "")}, {order.get("errorMessage", "")}'
        new_row[16] = order.get("shopBillId", "")

        shop_bill_id = new_row[16]

        if shop_bill_id in existing_orders_by_id:
            existing = existing_orders_by_id[shop_bill_id]
            if new_row != existing["row_data"]:
                rows_to_update.append((existing["row_number"], new_row))
        else:
            rows_to_append.append(new_row)

    if rows_to_update:
        batch_data = [
            {"range": f"A{row_number}:Y{row_number}", "values": [row_data]}
            for row_number, row_data in rows_to_update
        ]
        worksheet.batch_update(batch_data)
        print(f"🔁 Оновлено {len(rows_to_update)} рядків.")

    if rows_to_append:
        start_row = len(existing_rows) + 1
        worksheet.update(
            f"A{start_row}:Y{start_row + len(rows_to_append) - 1}",
            rows_to_append,
            value_input_option="USER_ENTERED"
        )
        print(f"➕ Додано {len(rows_to_append)} нових транзакцій з рядка {start_row}.")
    else:
        print("✅ Нових транзакцій для додавання немає.")


def export_portmone_orders_full():
    worksheet = init_google_sheet()

    CONFIG = config_manager()
    portmone_config = CONFIG.get("PORTMONE", [{}])[0]

    days = portmone_config.get("days", 5)

    try:
        days = int(days)
    except Exception:
        print(f"⚠️ Невірне значення days у конфігурації: {days}, використовую 5 днів")
        days = 5

    end = datetime.now()
    start = end - timedelta(days=days)

    max_days = 30
    delta = timedelta(days=max_days)

    current_start = start
    while current_start < end:
        current_end = min(current_start + delta, end)
        start_str = current_start.strftime("%d.%m.%Y")
        end_str = current_end.strftime("%d.%m.%Y")

        print(f"🔄 Обробка періоду {start_str} - {end_str}")

        orders = get_all_payment_statuses(start_str, end_str)
        if isinstance(orders, list):
            write_orders_to_sheet(worksheet, orders)
        else:
            print(f"❌ Неочікуваний формат замовлень за період {start_str} - {end_str}")

        current_start = current_end + timedelta(days=1)

    print("✅ Експорт завершено.")
