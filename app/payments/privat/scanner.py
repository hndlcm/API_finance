import logging
from datetime import datetime, timedelta
from typing import ClassVar

from ...constants import CURRENCY_CODES
from ...helpers.sync_rate_limiter import RateLimiter
from ...payment_config import PaymentItem
from ...schemas import TransactionRecord
from .api import PrivatApi
from .constants import API_ZONE_INFO
from .schemas import privat_transaction_to_record

logger = logging.getLogger(__name__)


class PrivatScanner:
    KEY: ClassVar[str] = "PRIVAT"

    def __init__(self, items: list[PaymentItem]):
        self._items = items
        self._limiter = RateLimiter(7, 1)

    def _work_with_item(self, item: PaymentItem) -> list[TransactionRecord]:
        api = PrivatApi(item.api_key, self._limiter)
        to_date_dt = datetime.now(API_ZONE_INFO)
        from_date_dt = to_date_dt - timedelta(days=item.days)

        logger.debug(
            'Scanning "%s"/"%s" between %s and %s',
            self.KEY,
            item.name,
            from_date_dt,
            to_date_dt,
        )

        balances = api.fetch_all_balances()
        acc_name_map = {b.acc: b.name_acc for b in balances}
        transactions = api.fetch_all_transactions(from_date_dt, to_date_dt)
        records = []
        for transaction in transactions:
            record = privat_transaction_to_record(
                transaction, acc_name_map, CURRENCY_CODES
            )
            records.append(record)
        return records

    def scan(self) -> list[TransactionRecord]:
        records = []
        for item in self._items:
            records.extend(self._work_with_item(item))
        return records
