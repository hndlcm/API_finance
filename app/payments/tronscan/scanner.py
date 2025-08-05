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

        transfers = api.fetch_all_transfers(item.address, from_date, to_date)
        records = [
            trc20_transfer_to_record(transfer, item.address)
            for transfer in transfers
        ]
        return records

    def scan(self) -> list[TransactionRecord]:
        records = []
        for item in self._items:
            records.extend(self._work_with_item(item))
        return records
