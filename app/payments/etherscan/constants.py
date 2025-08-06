from typing import Final

from requests import RequestException

API_URL: Final[str] = "https://api.etherscan.io/api"

DEFAULT_LIMIT: Final[int] = 100

RETRY_PARAMS: Final[dict] = {
    "on": (RequestException,),
    "delays": (0.2, 1, 20, 60),
}
