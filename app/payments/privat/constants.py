from typing import Final
from zoneinfo import ZoneInfo

BASE_URL: Final[str] = "https://acp.privatbank.ua/api"
TRANSACTIONS_URL: Final[str] = f"{BASE_URL}/statements/transactions"
BALANCE_URL: Final[str] = f"{BASE_URL}/statements/balance/final"

DT_FORMAT: Final[str] = "%d-%m-%Y"  # ДД-ММ-ГГГГ
DEFAULT_LIMIT: Final[int] = 100  # до 500, але 100 - рекомендоване

API_ZONE_INFO: Final[ZoneInfo] = ZoneInfo("Europe/Kyiv")
