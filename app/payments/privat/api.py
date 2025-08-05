"""
    Документація
    https://docs.google.com/document/d/e/2PACX-1vTtKvGa3P4E-lDqLg3bHRF6Wi9S7GIjSMFEFxII5qQZBGxuTXs25hQNiUU1hMZQhOyx6BNvIZ1bVKSr/pub
"""
import logging
from datetime import datetime

import requests

from ...helpers.retry_context import retry
from ...helpers.sync_rate_limiter import RateLimiter
from .constants import (
    BALANCE_URL,
    DEFAULT_LIMIT,
    DT_FORMAT,
    RETRY_PARAMS,
    TRANSACTIONS_URL,
)
from .schemas import Balance, BalancesPage, Transaction, TransactionsPage

logger = logging.getLogger(__name__)


class PrivatApi:
    def __init__(self, token: str, limiter: RateLimiter):
        self._token = token
        self._s = requests.Session()
        headers = {"User-Agent": "MyApp/1.0", "token": self._token}
        self._s.headers.update(headers)
        self._limiter = limiter

    @retry(logger, **RETRY_PARAMS)
    def fetch_transactions(
        self,
        start_date: datetime,
        end_date: datetime,
        follow_id: str | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> TransactionsPage:
        params = {
            "startDate": start_date.strftime(DT_FORMAT),
            "endDate": end_date.strftime(DT_FORMAT),
            "limit": limit,
        }
        if follow_id is not None:
            params["followId"] = follow_id

        self._limiter.wait()
        r = self._s.get(TRANSACTIONS_URL, params=params)
        r.raise_for_status()
        json_content = r.json()
        return TransactionsPage.model_validate(json_content)

    @retry(logger, **RETRY_PARAMS)
    def fetch_balances(
        self,
        follow_id: str | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> BalancesPage:
        params = {"limit": limit}
        if follow_id:
            params["followId"] = follow_id

        self._limiter.wait()
        r = self._s.get(BALANCE_URL, params=params)
        r.raise_for_status()
        json_content = r.json()
        return BalancesPage.model_validate(json_content)

    def fetch_all_transactions(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[Transaction]:
        transactions = []
        follow_id = None
        while True:
            page = self.fetch_transactions(start_date, end_date, follow_id)
            if page.status != "SUCCESS":
                raise RuntimeError("API balance повернуло помилку!")

            transactions.extend(page.transactions)
            if not page.exist_next_page:
                return transactions

            follow_id = page.next_page_id

    def fetch_all_balances(self) -> list[Balance]:
        balances = []
        follow_id = None
        while True:
            page = self.fetch_balances(follow_id)
            if page.status != "SUCCESS":
                raise RuntimeError("API balance повернуло помилку!")

            balances.extend(page.balances)
            if not page.exist_next_page:
                return balances

            follow_id = page.next_page_id
