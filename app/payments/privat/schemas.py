from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator

from ...schemas import TransactionRecord
from .constants import API_ZONE_INFO


class Transaction(BaseModel):
    ID: str | None = None
    # AUT_MY_CRF: str | None = None
    # AUT_MY_MFO: str | None = None
    AUT_MY_ACC: str | None = None
    # AUT_MY_NAM: str | None = None
    # AUT_MY_MFO_NAME: str | None = None
    # AUT_MY_MFO_CITY: str | None = None
    AUT_CNTR_CRF: str | None = None
    # AUT_CNTR_MFO: str | None = None
    AUT_CNTR_ACC: str | None = None
    AUT_CNTR_NAM: str | None = None
    # AUT_CNTR_MFO_NAME: str | None = None
    # AUT_CNTR_MFO_CITY: str | None = None
    CCY: str | None = None
    # FL_REAL: str | None = None
    # PR_PR: str | None = None
    # DOC_TYP: str | None = None
    # NUM_DOC: str | None = None
    # DAT_KL: str | None = None
    # DAT_OD: str | None = None
    OSND: str | None = None
    SUM: Decimal | None = None
    SUM_E: Decimal | None = None
    # REF: str | None = None
    # REFN: str | None = None
    # TIM_P: str | None = None
    DATE_TIME_DAT_OD_TIM_P: datetime | None = None
    TRANTYPE: str | None = None

    # DLR: str | None = None
    # TECHNICAL_TRANSACTION_ID: str | None = None
    # UETR: str | None = None
    # ULTMT: str | None = None
    # STRUCT_CODE: str | None = None

    @field_validator("DATE_TIME_DAT_OD_TIM_P", mode="before")
    def parse_datetime(cls, value):  # noqa
        if isinstance(value, str):
            dt = datetime.strptime(value, "%d.%m.%Y %H:%M:%S")
            return dt.replace(tzinfo=API_ZONE_INFO)
        return value


class TransactionsPage(BaseModel):
    status: str
    # # type: str | None = None
    exist_next_page: bool
    next_page_id: str | None = None
    transactions: list[Transaction] = []


class Balance(BaseModel):
    acc: str
    # currency: str | None = None
    # balanceIn: Decimal | None = None
    # balanceInEq: Decimal | None = None
    # balanceOut: Decimal | None = None
    # balanceOutEq: Decimal | None = None
    # turnoverDebt: Decimal | None = None
    # turnoverDebtEq: Decimal | None = None
    # turnoverCred: Decimal | None = None
    # turnoverCredEq: Decimal | None = None
    # bgfIBrnm: str | None = None
    # brnm: str | None = None
    # dpd: str | None = None
    name_acc: str = Field(alias="nameACC")
    # state: str | None = None
    # atp: str | None = None
    # flmn: str | None = None
    # date_open_acc_reg: str | None = None
    # date_open_acc_sys: str | None = None
    # date_close_acc: str | None = None
    # is_final_bal: bool | None = None


class BalancesPage(BaseModel):
    status: str
    # # type: str | None = None
    exist_next_page: bool
    next_page_id: str | None = None
    balances: list[Balance] = []


def privat_transaction_to_record(
    transaction: Transaction,
    acc_name_map: dict[str, str],
    currency_codes: dict[str, str],
) -> TransactionRecord:
    transaction_type = "debit" if transaction.TRANTYPE == "D" else "credit"

    return TransactionRecord(
        operation_datetime=(
            transaction.DATE_TIME_DAT_OD_TIM_P.astimezone(ZoneInfo("UTC"))
        ),  # 0
        bank_or_system="privatbank",  # 1
        account_name=acc_name_map.get(transaction.AUT_MY_ACC),  # 2
        account_number=transaction.AUT_MY_ACC,  # 3
        transaction_type=transaction_type,  # 4
        account_currency_amount=transaction.SUM_E,  # 5
        operation_currency_amount=transaction.SUM,  # 6
        currency=currency_codes.get(transaction.CCY, transaction.CCY),  # 7
        commission=None,  # 8
        balance_after_operation=None,  # 9
        operation_details=transaction.OSND,  # 10
        counterparty_details=transaction.AUT_CNTR_NAM,  # 11
        counterparty_code=transaction.AUT_CNTR_CRF,  # 12
        counterparty_account_number=transaction.AUT_CNTR_ACC,  # 13
        mcc=None,  # 14
        comment=None,  # 15
        transaction_id=transaction.ID,  # 16
    )
