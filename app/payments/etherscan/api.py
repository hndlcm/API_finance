import logging
from typing import Any

import requests

from ...helpers.retry_context import retry
from ...helpers.sync_rate_limiter import RateLimiter
from .constants import API_URL, DEFAULT_LIMIT, RETRY_PARAMS
from .schemas import Transaction, TransactionsPage

logger = logging.getLogger(__name__)


class ERC20Api:
    def __init__(self, token: str, limiter: RateLimiter):
        self._token = token
        self._s = requests.Session()
        self._limiter = limiter

    @retry(logger, **RETRY_PARAMS)
    def fetch_transactions(self, address: str, page: int) -> TransactionsPage:
        params: dict[str, Any] = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": page,
            "offset": DEFAULT_LIMIT,
            "sort": "asc",
            "apikey": self._token,
        }
        r = self._s.get(API_URL, params=params)
        r.raise_for_status()
        json_content = r.json()
        return TransactionsPage.model_validate(json_content)

    def fetch_all_transactions(self, address: str) -> list[Transaction]:
        transactions: list[Transaction] = []
        n = 1
        while True:
            page = self.fetch_transactions(address, n)
            if not page.result:
                return transactions

            transactions.extend(page.result)
            if len(page.result) < DEFAULT_LIMIT:
                return transactions

            n += 1
