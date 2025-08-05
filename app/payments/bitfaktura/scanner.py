import logging
from datetime import datetime, timedelta, timezone
from typing import ClassVar

from ...helpers.sync_rate_limiter import RateLimiter
from ...payment_config import PaymentItem
from ...schemas import TransactionRecord
from .api import BitfakturaApi
from .schemas import bitfaktura_invoice_to_record

logger = logging.getLogger(__name__)


class BitfakturaScanner:
    KEY: ClassVar[str] = "BITFACTURA"

    def __init__(self, items: list[PaymentItem]):
        self._items = items
        self._limiter = RateLimiter(7, 1)

    def _work_with_item(self, item: PaymentItem) -> list[TransactionRecord]:
        api = BitfakturaApi(item.api_key, self._limiter)

        to_date = datetime.now(timezone.utc)
        from_date = to_date - timedelta(days=item.days)

        logger.debug(
            'Scanning "%s"/"%s" between %s and %s',
            self.KEY,
            item.name,
            from_date,
            to_date,
        )

        invoices = api.fetch_all_invoices(from_date, to_date)
        records = [
            bitfaktura_invoice_to_record(invoice) for invoice in invoices
        ]
        return records

    def scan(self) -> list[TransactionRecord]:
        records = []
        for item in self._items:
            records.extend(self._work_with_item(item))
        return records
