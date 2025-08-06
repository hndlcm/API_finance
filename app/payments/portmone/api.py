import logging
from datetime import datetime, timedelta
from typing import Any

import requests

from ...helpers.misc import datetime_range_gen
from ...helpers.retry_context import retry
from ...helpers.sync_rate_limiter import RateLimiter
from .constants import GATEWAY_URL, MAX_PERIOD_IN_DAYS, RETRY_PARAMS
from .schemas import Payment

logger = logging.getLogger(__name__)


class PortmoneApi:
    def __init__(
        self,
        token: str,
        login: str,
        password: str,
        payee_id: int,
        limiter: RateLimiter,
    ):
        self._token = token
        self._s = requests.Session()
        self._login = login
        self._password = password
        self._payee_id = payee_id
        headers = {"User-Agent": "MyApp/1.0"}
        self._s.headers.update(headers)
        self._limiter = limiter

    @retry(logger, **RETRY_PARAMS)
    def fetch_payments(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[Payment]:
        payload: dict[str, Any] = {
            "method": "result",
            "params": {
                "data": {
                    "login": self._login,
                    "password": self._password,
                    "payeeId": self._payee_id,
                    "id": "123",
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                }
            },
        }
        self._limiter.wait()
        r = requests.post(GATEWAY_URL, json=payload)
        r.raise_for_status()
        json_content = r.json()
        return [Payment.model_validate(item) for item in json_content]

    def fetch_all_payments(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[Payment]:
        payments = []
        for start, end in datetime_range_gen(
            start_date, end_date, timedelta(days=MAX_PERIOD_IN_DAYS)
        ):
            payments.extend(self.fetch_payments(start, end))
        return payments
