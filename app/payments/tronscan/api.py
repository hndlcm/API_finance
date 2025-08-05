"""
   TODO:
     Можливо варто переглянути документацю API може інші запити дозволять
     вибирати напряму по діапазону дат.
     Наприклад: https://docs.tronscan.org/api-endpoints/transactions-and-transfers
"""

import logging
from collections.abc import Iterator

import requests

from ...helpers.retry_context import retry
from ...helpers.sync_rate_limiter import RateLimiter
from .constants import DEFAULT_LIMIT, RETRY_PARAMS, TRANSFERS_URL
from .schemas import TokenTransfer, TokenTransfersPage

logger = logging.getLogger(__name__)


class TransfersPageIterator:
    def __init__(
        self,
        api: "TRC20Api",
        address: str,
        start: int = 0,
        limit: int = DEFAULT_LIMIT,
    ):
        self._api = api
        self._address = address
        self._start = start
        self._limit = limit
        self._total = None

    def __iter__(self):
        return self

    def __next__(self):
        if self._total is not None and self._start >= self._total:
            raise StopIteration()

        page = self._api.fetch_transfers(
            self._address, self._start, self._limit
        )
        self._start += self._limit
        self._total = page.total
        return page


class TRC20Api:
    def __init__(self, token: str, limiter: RateLimiter):
        self._token = token
        self._s = requests.Session()
        headers = {"User-Agent": "MyApp/1.0", "TRON-PRO-API-KEY": token}
        self._s.headers.update(headers)
        self._limiter = limiter

    @retry(logger, **RETRY_PARAMS)
    def fetch_transfers(
        self,
        address,
        start=0,
        limit=DEFAULT_LIMIT,
    ) -> TokenTransfersPage:
        params = {
            "limit": limit,
            "start": start,
            "relatedAddress": address,
            "confirm": "true",
            "filterTokenValue": "1",
        }
        self._limiter.wait()
        r = self._s.get(TRANSFERS_URL, params=params)
        r.raise_for_status()
        json_content = r.json()
        return TokenTransfersPage(**json_content)

    def transfer_pages_iter(
        self,
        address: str,
        start: int = 0,
        limit: int = DEFAULT_LIMIT,
    ) -> Iterator[TokenTransfersPage]:
        return TransfersPageIterator(self, address, start, limit)

    def fetch_all_transfers(self, address: str) -> list[TokenTransfer]:
        transfers = []
        for page in self.transfer_pages_iter(address):
            transfers.extend(page.token_transfers)
        return transfers
