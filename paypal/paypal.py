import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Завантаження змінних з .env
load_dotenv()
CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
SECRET = os.getenv("PAYPAL_SECRET")

# PayPal API URL
BASE_URL = "https://api-m.sandbox.paypal.com"  # змінити на live для реального акаунту

def get_access_token():
    url = f"https://api-m.sandbox.paypal.com/v1/oauth2/token"
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}

    response = requests.post(url, headers=headers, data=data, auth=(CLIENT_ID, SECRET))
    response.raise_for_status()
    return response.json()["access_token"]

def get_transactions(access_token, start_date, end_date):
    headers = {
        'Authorization': f"Bearer {access_token}",
        'Content-Type': 'application/json',
    }

    params = (
        ('currency_code', 'ALL'),
        ('as_of_time', '2025-05-24T00:00:00-0700'),
        ('include_crypto_currencies', 'true'),
    )
    response = requests.get('https://api-m.sandbox.paypal.com/v1/reporting/balances', headers=headers, params=params)

    try:
        response.raise_for_status()
        data = response.json()
        return data.get("transaction_details", [])
    except requests.exceptions.HTTPError as e:
        print("HTTPError:", e)
        print("Response Text:", response.text)
        return []  # Повертаємо порожній список, щоб не було помилки в for
    # NB. Original query string below. It seems impossible to parse and
    # reproduce query strings 100% accurately so the one below is given
    # in case the reproduced version is not "correct".
    # response = requests.get('https://api-m.sandbox.paypal.com/v1/reporting/transactions?start_date=2014-07-12T00:00:00-0700&end_date=2014-07-12T23:59:59-0700&transaction_id=9GS80322P28628837&fields=all', headers=headers)


# Приклад використання
if __name__ == "__main__":
    token = get_access_token()
    print("Access Token:", token)
    headers = {
        "Authorization": f"Bearer {token}"
    }
    resp = requests.get(f"{BASE_URL}/v1/reporting/transactions", headers=headers)

    # Наприклад: останні 7 днів
    end = datetime.utcnow()
    start = end - timedelta(days=7)

    start_date = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    transactions = get_transactions(token, start_date, end_date)

    for txn in transactions:
        info = txn["transaction_info"]
        print(f"{info['transaction_id']} - {info['transaction_amount']['value']} {info['transaction_amount']['currency_code']}")