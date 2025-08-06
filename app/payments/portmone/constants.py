from typing import Final
from zoneinfo import ZoneInfo

from requests import RequestException

GATEWAY_URL: Final[str] = "https://www.portmone.com.ua/gateway/"

API_ZONE_INFO: Final[ZoneInfo] = ZoneInfo("Europe/Kyiv")

MAX_PERIOD_IN_DAYS: Final[int] = 31

RETRY_PARAMS: Final[dict] = {
    "on": (RequestException,),
    "delays": (0.2, 1, 20, 60),
}
