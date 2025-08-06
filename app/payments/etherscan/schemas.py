from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, Field

from ...schemas import TransactionRecord


class Transaction(BaseModel):
    block_number: str | None = Field(default=None, alias="blockNumber")
    timestamp: int = Field(alias="timeStamp")
    hash: str
    # nonce: str | None = None
    # block_hash: str | None = Field(default=None, alias="blockHash")
    from_address: str | None = Field(default=None, alias="from")
    # contract_address: str | None = Field(
    # default=None, alias="contractAddress"
    # )
    to_address: str = Field(alias="to")
    value: int
    token_name: str | None = Field(default=None, alias="tokenName")
    token_symbol: str | None = Field(default=None, alias="tokenSymbol")
    token_decimal: str = Field(alias="tokenDecimal")
    # transaction_index: str | None = Field(
    #     default=None, alias="transactionIndex"
    # )
    gas: str | None = None
    gas_price: str | None = Field(default=None, alias="gasPrice")
    gas_used: str | None = Field(default=None, alias="gasUsed")
    cumulative_gas_used: str | None = Field(
        default=None, alias="cumulativeGasUsed"
    )
    input: str | None = None
    method_id: str | None = Field(default=None, alias="methodId")
    function_name: str | None = Field(default=None, alias="functionName")
    confirmations: str | None = None

    @property
    def block_timestamp(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc)


class TransactionsPage(BaseModel):
    status: str | None = None
    message: str | None = None
    result: list[Transaction] = []


def erc20_transaction_to_record(
    transaction: Transaction, address: str
) -> TransactionRecord:
    transaction_type = (
        "debit"
        if transaction.to_address.casefold() == address.casefold()
        else "credit"
    )
    amount = abs(
        Decimal(transaction.value) / 10 ** int(transaction.token_decimal)
    )
    address_counterparty = (
        transaction.to_address
        if transaction_type == "credit"
        else transaction.from_address
    )

    return TransactionRecord(
        operation_datetime=transaction.block_timestamp,  # 0
        bank_or_system="ERC20",  # 1
        account_name=None,  # 2
        account_number=address,  # 3
        transaction_type=transaction_type,  # 4
        account_currency_amount=amount,  # 5
        operation_currency_amount=amount,  # 6
        currency=transaction.token_symbol,  # 7
        commission=None,  # 8
        balance_after_operation=None,  # 9
        operation_details=None,  # 10
        counterparty_details=None,  # 11
        counterparty_code=None,  # 12
        counterparty_account_number=address_counterparty,  # 13
        mcc=None,  # 14
        comment=None,  # 15
        transaction_id=transaction.hash,  # 16
    )
