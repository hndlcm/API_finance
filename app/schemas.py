from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class TransactionRecord(BaseModel):
    operation_datetime: datetime | None = None
    bank_or_system: str | None = None
    account_name: str | None = None
    account_number: str | None = None
    transaction_type: str | None = None
    account_currency_amount: Decimal | None = None
    operation_currency_amount: Decimal | None = None
    currency: str | None = None
    commission: Decimal | None = None
    balance_after_operation: Decimal | None = None
    operation_details: str | None = None
    counterparty_details: str | None = None
    counterparty_code: str | None = None
    counterparty_account_number: str | None = None
    mcc: int | None = None
    comment: str | None = None
    transaction_id: str
