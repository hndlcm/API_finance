from typing import Final

from requests import RequestException

BASE_URL: Final[str] = "https://handleua.bitfaktura.com.ua"
INVOICES_URL: Final[str] = f"{BASE_URL}/invoices.json"


RETRY_PARAMS: Final[dict] = {
    "on": (RequestException,),
    "delays": (0.2, 1, 20, 60),
}
