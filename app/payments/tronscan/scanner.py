import logging
from datetime import datetime, timedelta, timezone
from typing import ClassVar

# from ...constants import CURRENCY_CODES
from ...helpers.sync_rate_limiter import RateLimiter
from ...payment_config import PaymentItem
from ...schemas import TransactionRecord
from .api import TRC20Api
from .schemas import trc20_transfer_to_record

logger = logging.getLogger(__name__)


class TRC20Scanner:
    KEY: ClassVar[str] = "TRC20"

    def __init__(self, items: list[PaymentItem]):
        self._items = items
        self._limiter = RateLimiter(7, 1)

    def _work_with_item(self, item: PaymentItem) -> list[TransactionRecord]:
        api = TRC20Api(item.api_key, self._limiter)

        to_date = datetime.now(timezone.utc)
        from_date = to_date - timedelta(days=item.days)

        logger.debug(
            'Scanning "%s"/"%s" between %s and %s',
            self.KEY,
            item.name,
            from_date,
            to_date,
        )

        records = []
        is_last_page = False
        for page in api.transfer_pages_iter(item.address):
            for transfer in page.token_transfers:
                if from_date <= transfer.block_timestamp <= to_date:
                    records.append(
                        trc20_transfer_to_record(transfer, item.address)
                    )
                if transfer.block_timestamp < from_date:
                    is_last_page = True
            if is_last_page:
                break

        return records

    def scan(self) -> list[TransactionRecord]:
        records = []
        for item in self._items:
            records.extend(self._work_with_item(item))
        return records
