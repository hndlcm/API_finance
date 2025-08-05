from typing import Final

from requests import RequestException

BASE_URL: Final[str] = "https://apilist.tronscanapi.com"
TRANSFERS_URL: Final[str] = f"{BASE_URL}/api/new/token_trc20/transfers"
DEFAULT_LIMIT: Final[int] = 50

RETRY_PARAMS: Final[dict] = {
    "on": (RequestException,),
    "delays": (0.2, 1, 20, 60),
}
