from typing import Final

from requests import RequestException

BASE_URL: Final[str] = "https://api.monobank.ua"

CLIENT_INFO_URL: Final[str] = f"{BASE_URL}/personal/client-info"

TRANSACTION_URL_FMT: Final[str] = (
    f"{BASE_URL}" + "/personal/statement/{account_id}/{from_time}/{to_time}"
)

LIMIT: Final[int] = 500
MAX_PERIOD_SECONDS: Final[int] = 2682000  # 31 діб + 1 година


RETRY_PARAMS: Final[dict] = {
    "on": (RequestException,),
    "delays": (0.2, 1, 20, 60),
}
