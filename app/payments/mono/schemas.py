from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, Field

from ...schemas import TransactionRecord

# NOTE: MonoApi use "minor units" for money


class Account(BaseModel):
    id: str | None = None
    # send_id: str | None = Field(default=None, alias="sendId")
    currency_code: int | None = Field(default=None, alias="currencyCode")
    # cashback_type: str | None = Field(default=None, alias="cashbackType")
    # balance: int | None = None
    # credit_limit: int | None = Field(default=None, alias="creditLimit")
    # masked_pan: list[str] | None = Field(default=None, alias="maskedPan")
    # #type: str | None = None
    iban: str | None = None


class ClientInfo(BaseModel):
    client_id: str = Field(alias="clientId")
    name: str
    # web_hook_url: str | None = Field(default=None, alias="webHookUrl")
    # permissions: str | None = Field(default=None, alias="permissions")
    accounts: list[Account]


class Transaction(BaseModel):
    id: str
    time: int
    description: str | None = None
    mcc: int | None = None
    # original_mcc: int | None = Field(default=None, alias="originalMcc")
    amount: int | None = None
    operation_amount: int | None = Field(default=None, alias="operationAmount")
    currency_code: int | None = Field(default=None, alias="currencyCode")
    commission_rate: int | None = Field(default=None, alias="commissionRate")
    # cashback_amount: int | None = Field(default=None, alias="cashbackAmount")
    balance: int | None = None
    # hold: bool | None = None
    # receipt_id: str | None = Field(default=None, alias="receiptId")
    comment: str | None = None
    counter_name: str | None = Field(default=None, alias="counterName")
    counter_edrpou: str | None = Field(default=None, alias="counterEdrpou")
    counter_iban: str | None = Field(default=None, alias="counterIban")


def _from_minor_units(value: int | None) -> None | Decimal:
    """TODO: чи треба брати модуль числа?"""
    return value and abs(Decimal(value) / 100)


def mono_transaction_to_record(
    client_info: ClientInfo,
    account: Account,
    transaction: Transaction,
    currency_codes: dict[int, str],
) -> TransactionRecord:
    transaction_type = "debit" if (transaction.amount or 0) < 0 else "credit"

    currency_code = transaction.currency_code or account.currency_code
    currency = currency_codes.get(currency_code, currency_code)

    return TransactionRecord(
        operation_datetime=datetime.fromtimestamp(
            transaction.time, tz=timezone.utc
        ),  # 0
        bank_or_system="monobank",  # 1
        account_name=client_info.name,  # 2
        account_number=account.iban,  # 3
        transaction_type=transaction_type,  # 4
        account_currency_amount=_from_minor_units(transaction.amount),  # 5
        operation_currency_amount=_from_minor_units(
            transaction.operation_amount
        ),
        currency=currency,  # 7
        commission=_from_minor_units(transaction.commission_rate),  # 8
        balance_after_operation=_from_minor_units(transaction.balance),  # 9
        operation_details=transaction.comment,  # 10
        counterparty_details=transaction.counter_name,  # 11
        counterparty_code=transaction.counter_edrpou,  # 12
        counterparty_account_number=transaction.counter_iban,  # 13
        mcc=transaction.mcc,  # 14
        comment=transaction.description,  # 15
        transaction_id=transaction.id,  # 16
    )
