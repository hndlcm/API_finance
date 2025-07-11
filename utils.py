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
    url = "https://api.monobank.ua/bank/currency"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️ Не вдалося отримати курс валют: {response.status_code}")
            return []
    except Exception as e:
        print(f"⚠️ Помилка при запиті курсу валют: {e}")
        return []

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
