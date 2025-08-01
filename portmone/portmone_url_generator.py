import base64
import gzip
import json
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()
payee_id = os.getenv("PAYEE_ID")


def generate_portmone_url(data: dict) -> str:
    """
    Генерує посилання на оплату Portmone за допомогою GZIP + Base64 кодування параметра `i`.

    :param data: словник з параметрами оплати
    :return: URL для переадресації користувача
    """
    json_data = json.dumps(data, ensure_ascii=False)
    gzipped_data = gzip.compress(json_data.encode("utf-8"))
    base64_data = base64.b64encode(gzipped_data).decode("utf-8")
    i_param = quote_plus(base64_data)
    return f"https://www.portmone.com.ua/r3/uk/autoinsurance?i={i_param}"


# Приклад використання
if __name__ == "__main__":
    example_data = {
        "v": "2",
        "payeeId": payee_id,
        "lang": "uk",
        "amount": "100.31",
        "settings": {
            "period": "1",
            "payDate": "5",
            "startDate": "1.06.2025",
            "endDate": "20.07.2025",
        },
        "edit": "N",
        "description": "40-0111-078-2-5770640",
        "attribute1": "2019-08-01",
        "attribute2": "Іванов Олександр Олександрович",
        "attribute3": "Сплата страхових послуг згідно договору",
        "attribute4": "2710",
        "billNumber": "123-123-99",
        "emailAddress": "test@test.com",
        "timeToLive": "20",
        "contractDate": "11.06.2025",
        "limit": "12.06.2025",
        "successUrl": "https://portmone2.com/r3/ecommerce/test/master-test-form",
    }

    link = generate_portmone_url(example_data)
    print(link)
