from decimal import Decimal

from pydantic import BaseModel, Field


class TransactionRecord(BaseModel):
    source: str = Field(alias="дата время операции")  # 1 date time
    account_name: str = Field(alias="банк или система")  # 2
    account_number: str | None = Field(alias="название", default=None)  # 3
    account_id: str | None = Field(
        alias="номер идентификатор рахунку", default=None
    )  # 4
    transaction_type: str = Field(
        alias="тип операції"
    )  # 4 credit/debit/invoice/balance
    operation_amount: Decimal | None = Field(
        alias="сума в валюті рахунку", default=None
    )  # 5
    account_amount: Decimal | None = Field(
        alias="сума в валюті операции", default=None
    )  # 6
    account_currency: str | None = Field(alias="валюта", default=None)  # 7
    commission: Decimal | None = Field(alias="комісія", default=None)  # 8
    balance_after: Decimal | None = Field(
        alias="залишок після операції", default=None
    )  # 9
    osnd: str | None = Field(alias="деталі операції", default=None)  # 10
    counterparty_name: str | None = Field(
        alias="деталі котрагента", default=None
    )  # 11
    counterparty_crf: int | None = Field(
        alias="код котрагента", default=None
    )  # 12
    counterparty_account: str | None = Field(
        alias="номер идентификатор рахунку котрагента", default=None
    )  # 13
    comment: str | None = Field(alias="коммент", default=None)  # 15
    transaction_id: str = Field(alias="id транзакції")  # 16
