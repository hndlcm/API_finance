import logging
import time
from datetime import datetime
from typing import Final

import requests

from ...helpers.sync_rate_limiter import RateLimiter
from .schemas import ClientInfo, Transaction

BASE_URL: Final[str] = "https://api.monobank.ua"

CLIENT_INFO_URL: Final[str] = f"{BASE_URL}/personal/client-info"

TRANSACTION_URL_FMT: Final[str] = (
    f"{BASE_URL}" + "/personal/statement/{account_id}/{from_time}/{" "to_time}"
)

LIMIT: Final[int] = 500
MAX_PERIOD_SECONDS: Final[int] = 2682000  # 31 діб + 1 година

logger = logging.getLogger(__name__)


class TooManyRequestsError(RuntimeError):
    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class MonoApi:
    def __init__(self, token: str, limiter: RateLimiter):
        self._token = token
        self._s = requests.Session()
        headers = {"User-Agent": "MyApp/1.0", "X-Token": self._token}
        self._s.headers.update(headers)
        self._limiter = limiter

    def fetch_client_info(self) -> ClientInfo:
        self._limiter.wait()
        r = self._s.get(CLIENT_INFO_URL)
        r.raise_for_status()
        json_content = r.json()
        return ClientInfo.model_validate(json_content)

    def fetch_transactions(
        self,
        account_id: str,
        from_unix_time: int,
        to_unix_time: int,
    ) -> list[Transaction]:
        logger.debug("time %d %d", from_unix_time, to_unix_time)
        self._limiter.wait()
        r = self._s.get(
            TRANSACTION_URL_FMT.format(
                account_id=account_id,
                from_time=from_unix_time,
                to_time=to_unix_time,
            )
        )
        if r.status_code == 429:  # HTTPError: 429 Too Many Requests
            value = r.headers.get("Retry-After")
            retry_after = float(value) if value is not None else None
            raise TooManyRequestsError("Too Many Requests", retry_after)
        r.raise_for_status()
        json_content = r.json()
        return [Transaction.model_validate(data) for data in json_content]

    def fetch_all_transactions(
        self,
        account_id: str,
        from_time: datetime,
        to_time: datetime,
    ) -> list[Transaction]:
        all_transactions = []

        from_unix_time = int(from_time.timestamp())
        current_to_unix_time = int(to_time.timestamp())

        while current_to_unix_time > from_unix_time:
            max_from_for_chunk = current_to_unix_time - MAX_PERIOD_SECONDS
            chunk_from_unix_time = max(from_unix_time, max_from_for_chunk)

            while True:
                try:
                    transactions = self.fetch_transactions(
                        account_id,
                        chunk_from_unix_time,
                        current_to_unix_time,
                    )
                    all_transactions.extend(transactions)

                    if len(transactions) < LIMIT:
                        break

                    last_transaction = transactions[-1]
                    if last_transaction.time <= chunk_from_unix_time:
                        break

                    current_to_unix_time = last_transaction.time
                except TooManyRequestsError as e:
                    logger.warning("%s %s", type(e), e)
                    if e.retry_after is None:
                        logger.debug("Retry after: 60s")
                        time.sleep(60)
                    else:
                        logger.debug("Retry after: %ds", e.retry_after)
                        time.sleep(e.retry_after)

            current_to_unix_time = chunk_from_unix_time

        return all_transactions
