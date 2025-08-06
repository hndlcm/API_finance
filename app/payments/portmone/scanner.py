import logging
from datetime import datetime, timedelta
from typing import ClassVar

from ...helpers.sync_rate_limiter import RateLimiter
from ...payment_config import PaymentItem
from ...schemas import TransactionRecord
from .api import PortmoneApi
from .constants import API_ZONE_INFO
from .schemas import portmone_payment_to_record

logger = logging.getLogger(__name__)


class PortmoneScanner:
    KEY: ClassVar[str] = "PORTMONE"

    def __init__(self, items: list[PaymentItem]):
        self._items = items
        self._limiter = RateLimiter(7, 1)

    def _work_with_item(self, item: PaymentItem) -> list[TransactionRecord]:
        api = PortmoneApi(
            item.api_key,
            item.login,
            item.password,
            item.payee_id,
            self._limiter,
        )
        to_date = datetime.now(API_ZONE_INFO)
        from_date = to_date - timedelta(days=item.days)

        logger.info(
            'Scanning "%s"/"%s" between %s and %s',
            self.KEY,
            item.name,
            from_date,
            to_date,
        )

        payments = api.fetch_all_payments(from_date, to_date)
        records = [portmone_payment_to_record(p) for p in payments]
        return records

    def scan(self) -> list[TransactionRecord]:
        records = []
        for item in self._items:
            records.extend(self._work_with_item(item))
        return records
