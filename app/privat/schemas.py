from decimal import Decimal

from pydantic import BaseModel
from schemas import TransactionRecord


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
    # DATE_TIME_DAT_OD_TIM_P: str | None = None
    TRANTYPE: str | None = None
    # DLR: str | None = None
    # TECHNICAL_TRANSACTION_ID: str | None = None
    # UETR: str | None = None
    # ULTMT: str | None = None
    # STRUCT_CODE: str | None = None


class TransactionResponse(BaseModel):
    status: str
    ## type: str | None = None
    exist_next_page: bool
    next_page_id: str | None = None
    transactions: list[Transaction] = []


class Balance(BaseModel):
    acc: str | None = None
    currency: str | None = None
    balanceIn: Decimal | None = None
    balanceInEq: Decimal | None = None
    balanceOut: Decimal | None = None
    balanceOutEq: Decimal | None = None
    turnoverDebt: Decimal | None = None
    turnoverDebtEq: Decimal | None = None
    turnoverCred: Decimal | None = None
    turnoverCredEq: Decimal | None = None
    bgfIBrnm: str | None = None
    brnm: str | None = None
    dpd: str | None = None
    nameACC: str | None = None
    state: str | None = None
    atp: str | None = None
    flmn: str | None = None
    date_open_acc_reg: str | None = None
    date_open_acc_sys: str | None = None
    date_close_acc: str | None = None
    is_final_bal: bool | None = None


class BalanceResponse(BaseModel):
    status: str
    ## type: str | None = None
    exist_next_page: bool
    next_page_id: str | None = None
    balances: list[Balance] = []


def map_transaction_to_row(
    transaction: Transaction,
    acc_name_map: dict[str, str],
    currency_codes: dict[str, str],
) -> TransactionRecord:
    source = ""
    dat_od = transaction.DAT_OD or ""
    tim_p = transaction.TIM_P or ""
    if dat_od or tim_p:
        source = f"{dat_od} {tim_p}".strip()

    account_number = transaction.AUT_MY_ACC or ""
    account_name = acc_name_map.get(account_number, "")
    transaction_type = "debit" if transaction.TRANTYPE == "D" else "credit"
    operation_amount = transaction.SUM or Decimal("0")
    account_amount = transaction.SUM_E or Decimal("0")
    account_currency = currency_codes.get(
        transaction.CCY or "UAH", transaction.CCY or "UAH"
    )

    try:
        counterparty_crf = int(transaction.AUT_CNTR_CRF or "0")
    except ValueError:
        counterparty_crf = 0

    return TransactionRecord(
        source=source,
        account_name=account_name,
        account_number=account_number,
        account_id=account_number,
        transaction_type=transaction_type,
        operation_amount=operation_amount,
        account_amount=account_amount,
        account_currency=account_currency,
        commission=None,
        balance_after=None,
        osnd=transaction.OSND,
        counterparty_name=transaction.AUT_CNTR_NAM,
        counterparty_crf=counterparty_crf,
        counterparty_account=transaction.AUT_CNTR_ACC,
        mcc=None,
        comment=None,
        transaction_id=transaction.ID,
    )
