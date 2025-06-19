import os
from dotenv import load_dotenv
import requests
import time
import json

load_dotenv()
TOKEN = os.getenv('MONO')

ACCOUNT = '0aNgqwLmPXxbHltHEMrUJg'  # 🔄 заміни на свій account ID, отриманий із /client-info
BASE_URL = 'https://api.monobank.ua/personal/statement/{account}/{from_time}/{to_time}'

HEADERS = {
    'X-Token': TOKEN
}

def get_monobank_statements(account, from_time, to_time):
    all_transactions = []

    while True:
        url = BASE_URL.format(account=account, from_time=from_time, to_time=to_time)
        print(f"GET: {url}")
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text}")
            break

        transactions = response.json()
        all_transactions.extend(transactions)

        if len(transactions) < 500:
            break

        # Зменшення to_time до останньої транзакції
        last_tx_time = transactions[-1]['time']
        to_time = last_tx_time

        print(f"↪️ Отримано 500 транзакцій, новий to_time = {to_time}")
        time.sleep(60)  # дотримання обмеження MonoBank (1 запит/60с)

    return all_transactions

# 🕒 Встановлення періоду
current_time = int(time.time())
from_time = current_time - 7 * 24 * 60 * 60  # останні 7 днів
to_time = current_time

# 📥 Виклик функції
transactions = get_monobank_statements(ACCOUNT, from_time, to_time)

# 💾 Збереження в JSON-файл
with open('monobank_transactions.json', 'w', encoding='utf-8') as f:
    json.dump(transactions, f, ensure_ascii=False, indent=4)

print(f"\n✅ Отримано всього {len(transactions)} транзакцій.")
print("📄 Збережено у файл monobank_transactions.json")
