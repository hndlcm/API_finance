from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, Field

from ...schemas import TransactionRecord


class TokenInfo(BaseModel):
    token_id: str = Field(alias="tokenId")
    token_abbr: str = Field(alias="tokenAbbr")
    token_name: str = Field(alias="tokenName")
    token_decimal: int = Field(alias="tokenDecimal")
    # token_can_show: int | None = Field(default=None, alias="tokenCanShow")
    # token_type: str | None = Field(default=None, alias="tokenType")
    # token_logo: str | None = Field(default=None, alias="tokenLogo")
    # token_level: str | None = Field(default=None, alias="tokenLevel")
    # issuer_addr: str | None = Field(default=None, alias="issuerAddr")
    # vip: bool | None = None


class TokenTransfer(BaseModel):
    transaction_id: str
    # status: int | None = None
    block_ts: int
    from_address: str | None = None
    # from_address_tag: dict | None = None
    to_address: str
    # to_address_tag: dict | None = None
    # block: int | None = None
    contract_address: str | None = None
    quant: Decimal
    # confirmed: bool | None = None
    # contract_ret: str | None = Field(default=None, alias="contractRet")
    # final_result: str | None = Field(default=None, alias="finalResult")
    # revert: bool | None = None
    token_info: TokenInfo = Field(alias="tokenInfo")

    # contract_type: str | None = None
    # from_address_is_contract: bool | None = Field(
    #    default=None, alias="fromAddressIsContract"
    # )
    # to_address_is_contract: bool | None = Field(
    #     default=None, alias="toAddressIsContract"
    # )
    # risk_transaction: bool | None = Field(
    #    default=None, alias="riskTransaction"
    # )

    @property
    def block_timestamp(self) -> datetime:
        return datetime.fromtimestamp(self.block_ts / 1000, tz=timezone.utc)


class TokenTransfersPage(BaseModel):
    total: int
    range_total: int | None = Field(default=None, alias="rangeTotal")
    contract_info: dict | None = Field(default=None, alias="contractInfo")
    token_transfers: list[TokenTransfer] = []
    time_interval: int | None = Field(default=None, alias="timeInterval")
    normal_address_info: dict[str, dict[str, bool]] | None = Field(
        default=None, alias="normalAddressInfo"
    )


def trc20_transfer_to_record(
    transfer: TokenTransfer, address: str
) -> TransactionRecord:
    transaction_type = (
        "debit"
        if transfer.to_address.casefold() == address.casefold()
        else "credit"
    )
    amount = abs(transfer.quant / 10 ** int(transfer.token_info.token_decimal))
    address_counterparty = (
        transfer.to_address
        if transaction_type == "credit"
        else transfer.from_address
    )

    return TransactionRecord(
        operation_datetime=transfer.block_timestamp,  # 0
        bank_or_system="TRC20",  # 1
        account_name=None,  # 2
        account_number=address,  # 3
        transaction_type=transaction_type,  # 4
        account_currency_amount=amount,  # 5
        operation_currency_amount=amount,  # 6
        currency=transfer.token_info.token_abbr,  # 7
        commission=None,  # 8 # FIXME: що таке fee у попередньому коді ?
        balance_after_operation=None,  # 9
        operation_details=None,  # 10
        counterparty_details=None,  # 11
        counterparty_code=None,  # 12
        counterparty_account_number=address_counterparty,  # 13
        mcc=None,  # 14
        comment=None,  # 15
        transaction_id=transfer.transaction_id,  # 16
    )
