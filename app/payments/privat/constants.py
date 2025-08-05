from typing import Final
from zoneinfo import ZoneInfo

from requests import RequestException

BASE_URL: Final[str] = "https://acp.privatbank.ua/api"
TRANSACTIONS_URL: Final[str] = f"{BASE_URL}/statements/transactions"
BALANCE_URL: Final[str] = f"{BASE_URL}/statements/balance/final"

DT_FORMAT: Final[str] = "%d-%m-%Y"  # ДД-ММ-ГГГГ
DEFAULT_LIMIT: Final[int] = 100  # до 500, але 100 - рекомендоване

API_ZONE_INFO: Final[ZoneInfo] = ZoneInfo("Europe/Kyiv")

RETRY_PARAMS: Final[dict] = {
    "on": (RequestException,),
    "delays": (0.2, 1, 20, 60),
}
