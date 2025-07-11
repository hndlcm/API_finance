import requests
from datetime import datetime

def datetime_to_serial_float(dt: datetime) -> float:
    epoch = datetime(1899, 12, 30)
    return (dt - epoch).total_seconds() / 86400

def format_amount(value):
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.0

def get_mono_exchange_rates():
    response = requests.get("https://api.monobank.ua/bank/currency")
    if response.status_code == 200:
        data = response.json()
        for rate in data:
            print(rate)
    else:
        print(f"Помилка: {response.status_code}")


def convert_currency(amount, from_ccy, to_ccy, rates):
    if from_ccy == to_ccy:
        return amount
    for rate in rates:
        a = rate.get("currencyCodeA")
        b = rate.get("currencyCodeB")
        r = rate.get("rateSell") or rate.get("rateCross")
        if a == from_ccy and b == to_ccy and r:
            return round(amount * r, 2)
        if b == from_ccy and a == to_ccy and r:
            return round(amount / r, 2)
    print(f"⚠️ Курс для {from_ccy}->{to_ccy} не знайдено")
    return amount
