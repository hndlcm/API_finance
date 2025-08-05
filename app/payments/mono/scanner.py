import logging
from datetime import datetime, timedelta, timezone
from typing import ClassVar

from ...constants import CURRENCY_CODES
from ...helpers.sync_rate_limiter import RateLimiter
from ...payment_config import PaymentItem
from ...schemas import TransactionRecord
from .api import MonoApi
from .schemas import mono_transaction_to_record

logger = logging.getLogger(__name__)


class MonoScanner:
    KEY: ClassVar[str] = "MONO"

    def __init__(self, items: list[PaymentItem]):
        self._items = items
        self._limiter = RateLimiter(7, 60)
        # Для транзакцій ліміт 1 запит на 60 с
        # Але простіше робити до 7 запитів отримувати помилку - чекати 60 с
        # і повторювати запити

    def _work_with_item(self, item: PaymentItem) -> list[TransactionRecord]:
        api = MonoApi(item.api_key, self._limiter)

        to_date = datetime.now(timezone.utc)
        from_date = to_date - timedelta(days=item.days)

        logger.debug(
            'Scanning "%s"/"%s" between %s and %s',
            self.KEY,
            item.name,
            from_date,
            to_date,
        )

        client_info = api.fetch_client_info()
        records = []

        for account in client_info.accounts:
            transactions = api.fetch_all_transactions(
                account.id, from_date, to_date
            )
            for transaction in transactions:
                record = mono_transaction_to_record(
                    client_info, account, transaction, CURRENCY_CODES
                )
                records.append(record)
        return records

    def scan(self) -> list[TransactionRecord]:
        records = []
        for item in self._items:
            records.extend(self._work_with_item(item))
        return records
