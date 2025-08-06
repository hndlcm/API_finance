import logging
from typing import Any

import requests

from ...helpers.retry_context import retry
from ...helpers.sync_rate_limiter import RateLimiter
from .constants import INVOICES_URL, RETRY_PARAMS
from .schemas import Invoice

logger = logging.getLogger(__name__)


class BitfakturaApi:
    def __init__(self, token: str, limiter: RateLimiter):
        self._token = token
        self._s = requests.Session()
        self._limiter = limiter

    @retry(logger, **RETRY_PARAMS)
    def fetch_invoices(self, page: int) -> list[Invoice]:
        params: dict[str, Any] = {
            "api_token": self._token,
            "page": page,
        }
        self._limiter.wait()
        r = self._s.get(INVOICES_URL, params=params)
        r.raise_for_status()
        json_content = r.json()
        return [Invoice.model_validate(item) for item in json_content]

    def fetch_all_invoices(self) -> list[Invoice]:
        page = 1
        all_invoices: list[Invoice] = []
        while True:
            invoices = self.fetch_invoices(page)
            if not invoices:
                return all_invoices

            all_invoices.extend(invoices)
            page += 1
