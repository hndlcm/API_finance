from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from ...schemas import TransactionRecord
from .constants import API_ZONE_INFO


class Payment(BaseModel):
    payee_id: str
    description: str | None = None
    status: str
    # attribute1: str | None = None
    # attribute2: str | None = None
    # attribute3: str | None = None
    # attribute4: str | None = None
    # attribute5: str | None = None
    commission: Decimal | None = None
    # distribution_payee_id: str | None = None
    # bank_name: str | None = None
    # terminal_id: str | None = None
    # merchant_id: str | None = None
    # rrn: str | None = None
    pay_date: datetime
    # payee_export_date: datetime | None = None
    # payee_export_flag: str | None = None
    # chargeback: str | None = None
    payee_name: str | None = None
    payee_commission: Decimal | None = None
    # pay_order_date: datetime | None = None
    # pay_order_number: str | None = None
    pay_order_amount: Decimal | None = None
    shop_bill_id: str = Field(alias="shopBillId")
    # shop_order_number: str | None = Field(
    #    default=None, alias="shopOrderNumber"
    # )
    bill_amount: Decimal | None = Field(default=None, alias="billAmount")
    error_code: str | None = Field(default=None, alias="errorCode")
    error_message: str | None = Field(default=None, alias="errorMessage")
    # auth_code: str | None = Field(default=None, alias="authCode")
    card_mask: str | None = Field(default=None, alias="cardMask")
    card_bank_name: str | None = Field(default=None, alias="cardBankName")
    # token: str | None = None
    # payee_export_result: str | None = Field(
    #     default=None, alias="payeeExportResult"
    # )
    gate_type: str | None = Field(default=None, alias="gateType")
    card_type_name: str | None = Field(default=None, alias="cardTypeName")

    @field_validator("pay_date", mode="before")
    def parse_datetime(cls, value):  # noqa
        if isinstance(value, str):
            dt = datetime.strptime(value, "%d.%m.%Y %H:%M:%S")
            return dt.replace(tzinfo=API_ZONE_INFO)
        return value

    @field_validator("pay_order_amount", mode="before")
    def parse_decimal(cls, value):  # noqa
        if isinstance(value, str):
            return Decimal(value) if value else None
        return value


def portmone_payment_to_record(payment: Payment) -> TransactionRecord:
    transaction_type = (
        "debit"
        if payment.status == "PAYED"
        else "invoice"
        if payment.status == "CREATED"
        else payment.status
    )
    counterparty_details = ", ".join(
        (
            payment.card_bank_name or "",
            payment.card_type_name or "",
            payment.gate_type or "",
        )
    )
    comment = ", ".join(
        (
            payment.error_code or "",
            payment.error_message or "",
        )
    )
    amount = payment.bill_amount and abs(payment.bill_amount)

    return TransactionRecord(
        operation_datetime=payment.pay_date,  # 0
        bank_or_system="portmone",  # 1
        account_name=payment.payee_name,  # 2
        account_number=None,  # 3
        transaction_type=transaction_type,  # 4
        account_currency_amount=amount,  # 5
        operation_currency_amount=amount,  # 6
        currency="UAH",  # 7
        commission=payment.payee_commission and abs(payment.payee_commission),
        balance_after_operation=None,  # 9
        operation_details=payment.description,  # 10
        counterparty_details=counterparty_details,  # 11
        counterparty_code=None,  # 12
        counterparty_account_number=payment.card_mask,  # 13
        mcc=None,  # 14
        comment=comment,  # 15
        transaction_id=payment.shop_bill_id,  # 16
    )
