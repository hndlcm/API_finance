import logging
from datetime import datetime

import requests

from ...helpers.retry_context import retry
from ...helpers.sync_rate_limiter import RateLimiter
from .constants import INVOICES_URL, RETRY_PARAMS
from .schemas import Invoice

logger = logging.getLogger(__name__)


class FacturowniaApi:
    def __init__(self, token: str, limiter: RateLimiter):
        self._token = token
        self._s = requests.Session()
        self._limiter = limiter

    @retry(logger, **RETRY_PARAMS)
    def fetch_invoices(self, page: int) -> list[Invoice]:
        params = {"api_token": self._token, "page": page}
        self._limiter.wait()
        r = self._s.get(INVOICES_URL, params=params)
        r.raise_for_status()
        json_content = r.json()
        return [Invoice.model_validate(item) for item in json_content]

    def fetch_all_invoices(
        self,
        start_data: datetime,
        end_date: datetime,
    ) -> list[Invoice]:
        #  TODO:
        #    мабуть не дуже добре вигрібати все і фільтрувати,
        #    варто подивитись документацію api чи нема фільтації по даті
        page = 1
        all_invoices = []
        while True:
            invoices = self.fetch_invoices(page)
            for invoice in invoices:
                if start_data <= invoice.updated_at <= end_date:
                    all_invoices.extend(invoices)
            if not invoices:
                break
            page += 1
        return all_invoices
