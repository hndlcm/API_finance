import logging
from datetime import datetime, timedelta, timezone
from typing import ClassVar

from ...helpers.sync_rate_limiter import RateLimiter
from ...payment_config import PaymentItem
from ...schemas import TransactionRecord
from .api import ERC20Api
from .schemas import erc20_transaction_to_record

logger = logging.getLogger(__name__)


class ERC20Scanner:
    KEY: ClassVar[str] = "ERC20"

    def __init__(self, items: list[PaymentItem]):
        self._items = items
        self._limiter = RateLimiter(2, 1)

    def _work_with_item(self, item: PaymentItem) -> list[TransactionRecord]:
        api = ERC20Api(item.api_key, self._limiter)

        to_date = datetime.now(timezone.utc)
        from_date = to_date - timedelta(days=365)  # item.days

        logger.debug(
            'Scanning "%s"/"%s" between %s and %s',
            self.KEY,
            item.name,
            from_date,
            to_date,
        )

        item.address = "0x19Cf249E7e423b5Bd2d41FD62e7f3adbfdEe5B47"

        transactions = api.fetch_all_transactions(item.address)
        logger.debug("transactions: %d", len(transactions))
        records = []
        for transaction in transactions:
            if from_date <= transaction.block_timestamp <= to_date:
                record = erc20_transaction_to_record(transaction, item.address)
                records.append(record)

        return records

    def scan(self) -> list[TransactionRecord]:
        records = []
        for item in self._items:
            records.extend(self._work_with_item(item))
            break
        return records
