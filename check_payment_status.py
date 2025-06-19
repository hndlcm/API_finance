import requests
import time
import json
import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from table import init_google_sheet


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


def get_all_payment_statuses(start_date: str, end_date: str):
    load_dotenv()
    PORTMONE_URL = "https://www.portmone.com.ua/gateway/"
    PAYEE_ID = os.getenv("PAYEE_ID")
    LOGIN = os.getenv("PORTMONE_LOGIN")
    PASSWORD = os.getenv("PORTMONE_PASSWORD")

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

        with open("portmone_all_orders.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        return data if isinstance(data, list) else []

    except requests.exceptions.RequestException as e:
        error_data = {"status": "error", "message": str(e)}
        with open("portmone_error.json", "w", encoding="utf-8") as f:
            json.dump(error_data, f, ensure_ascii=False, indent=4)
        return []


def write_orders_to_sheet(worksheet, orders: list):
    try:
        existing_rows = worksheet.get_all_values()
    except Exception as e:
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
        new_row[0] = format_date(order.get("pay_date", ""))
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
        new_row[
            11] = f"""{order.get("cardBankName", "")}, {order.get("cardTypeName", "")}, {order.get("gateType", "")}"""
        new_row[13] = order.get("cardMask", "")
        new_row[15] = f"""{order.get("errorCode", "")}, {order.get("errorMessage", "")}"""
        new_row[16] = order.get("shopBillId", "")

        shop_bill_id = new_row[16]

        if shop_bill_id in existing_orders_by_id:
            existing = existing_orders_by_id[shop_bill_id]
            if new_row != existing["row_data"]:
                rows_to_update.append((existing["row_number"], new_row))
        else:
            rows_to_append.append(new_row)

    # --- Оновлення рядків через batch_update ---
    batch_data = [
        {
            "range": f"A{row_number}:Y{row_number}",
            "values": [row_data]
        }
        for row_number, row_data in rows_to_update
    ]
    if batch_data:
        worksheet.batch_update(batch_data)
        print(f"🔁 Оновлено {len(batch_data)} рядків.")

    # --- Додавання нових ---
    if rows_to_append:
        start_row = len(existing_rows) + 1
        worksheet.update(f"A{start_row}:Y{start_row + len(rows_to_append) - 1}", rows_to_append)
        print(f"➕ Додано {len(rows_to_append)} нових транзакцій починаючи з рядка {start_row}.")
    else:
        print("✅ Нових транзакцій для додавання немає.")


def export_portmone_orders(start_date: str, end_date: str):
    worksheet = init_google_sheet()
    orders = get_all_payment_statuses(start_date, end_date)
    write_orders_to_sheet(worksheet, orders)
