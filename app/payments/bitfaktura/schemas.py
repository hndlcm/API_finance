from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from ...schemas import TransactionRecord

# class CalculatingStrategy(BaseModel):
#     position: str | None = None
#     sum: str | None = None
#     invoice_form_price_kind: str | None = None


class Invoice(BaseModel):
    id: int
    number: str | None = None
    price_gross: Decimal | None = None
    currency: str | None = None
    created_at: datetime
    updated_at: datetime
    seller_bank_account: str | None = None
    buyer_bank_account: str | None = None
    buyer_name: str | None = None
    buyer_tax_no: str | None = None
    # user_id: int | None = None
    # app: Any = None
    # place: str | None = None
    # sell_date: date | None = None
    # payment_type: str | None = None
    # price_net: Decimal | None = None
    # status: str | None = None
    # description: str | None = None
    # seller_name: str | None = None
    # seller_tax_no: str | None = None
    # seller_street: str | None = None
    # seller_post_code: str | None = None
    # seller_city: str | None = None
    # seller_country: str | None = None
    # seller_email: str | None = None
    # seller_phone: str | None = None
    # seller_fax: str | None = None
    # seller_www: str | None = None
    # seller_person: str | None = None
    # seller_bank: str | None = None
    # buyer_post_code: str | None = None
    # buyer_city: str | None = None
    # buyer_street: str | None = None
    # buyer_first_name: str | None = None
    # buyer_country: str | None = None
    # token: str | None = None
    # buyer_email: str | None = None
    # buyer_www: str | None = None
    # buyer_fax: str | None = None
    # buyer_phone: str | None = None
    # kind: str | None = None
    # pattern: str | None = None
    # pattern_nr: int | None = None
    # pattern_nr_m: int | None = None
    # pattern_nr_d: int | None = None
    # client_id: int | None = None
    # payment_to: date | None = None
    # paid: Decimal | None = None
    # seller_bank_account_id: int | None = None
    # lang: str | None = None
    # issue_date: date | None = None
    # price_tax: Decimal | None = None
    # department_id: int | None = None
    # correction: Any = None
    # buyer_note: str | None = None
    # additional_info_desc: str | None = None
    # additional_info: bool | None = None
    # product_cache: str | None = None
    # buyer_last_name: str | None = None
    # from_invoice_id: int | None = None
    # oid: str | None = None
    # discount: Decimal | None = None
    # show_discount: bool | None = None
    # sent_time: datetime | None = None
    # print_time: datetime | None = None
    # recurring_id: int | None = None
    # tax2_visible: bool | None = None
    # warehouse_id: int | None = None
    # paid_date: date | None = None
    # product_id: int | None = None
    # issue_year: int | None = None
    # internal_note: str | None = None
    # invoice_id: int | None = None
    # invoice_template_id: int | None = None
    # description_long: str | None = None
    # buyer_tax_no_kind: str | None = None
    # seller_tax_no_kind: str | None = None
    # description_footer: str | None = None
    # sell_date_kind: str | None = None
    # payment_to_kind: str | None = None
    # exchange_currency: str | None = None
    # discount_kind: str | None = None
    # income: bool | None = None
    # from_api: bool | None = None
    # category_id: int | None = None
    # warehouse_document_id: int | None = None
    # exchange_kind: str | None = None
    # exchange_rate: Decimal | None = None
    # use_delivery_address: bool | None = None
    # delivery_address: str | None = None
    # accounting_kind: str | None = None
    # buyer_person: str | None = None
    # buyer_bank_account: str | None = None
    # buyer_bank: str | None = None
    # buyer_mass_payment_code: str | None = None
    # exchange_note: str | None = None
    # buyer_company: bool | None = None
    # show_attachments: bool | None = None
    # exchange_currency_rate: Decimal | None = None
    # has_attachments: bool | None = None
    # exchange_date: date | None = None
    # attachments_count: int | None = None
    # delivery_date: date | None = None
    # fiscal_status: str | None = None
    # use_moss: bool | None = None
    # calculating_strategy: CalculatingStrategy | None = None
    # transaction_date: date | None = None
    # email_status: str | None = None
    # exclude_from_stock_level: bool | None = None
    # exclude_from_accounting: bool | None = None
    # exchange_rate_den: Decimal | None = None
    # exchange_currency_rate_den: Decimal | None = None
    # accounting_scheme: str | None = None
    # exchange_difference: Decimal | None = None
    # not_cost: bool | None = None
    # reverse_charge: bool | None = None
    # issuer: str | None = None
    # use_issuer: bool | None = None
    # cancelled: bool | None = None
    # recipient_id: int | None = None
    # recipient_name: str | None = None
    # test: bool | None = None
    # discount_net: Decimal | None = None
    # approval_status: str | None = None
    # accounting_vat_tax_date: date | None = None
    # accounting_income_tax_date: date | None = None
    # accounting_other_tax_date: date | None = None
    # accounting_status: str | None = None
    # normalized_number: str | None = None
    # na_tax_kind: str | None = None
    # issued_to_receipt: bool | None = None
    # gov_id: int | None = None
    # gov_kind: str | None = None
    # gov_status: str | None = None
    # sales_code: str | None = None
    # additional_invoice_field: str | None = None
    # products_margin: Decimal | None = None
    # payment_url: str | None = None
    # view_url: str | None = None
    # buyer_mobile_phone: str | None = None
    # kind_text: str | None = None
    # invoice_for_receipt_id: int | None = None
    # receipt_for_invoice_id: int | None = None
    # recipient_company: str | None = None
    # recipient_first_name: str | None = None
    # recipient_last_name: str | None = None
    # recipient_tax_no: str | None = None
    # recipient_street: str | None = None
    # recipient_post_code: str | None = None
    # recipient_city: str | None = None
    # recipient_country: str | None = None
    # recipient_email: str | None = None
    # recipient_phone: str | None = None
    # recipient_note: str | None = None
    # overdue_: bool | None = Field(alias="overdue?")
    # get_tax_name: str | None = None
    # tax_visible_: bool | None = Field(alias="tax_visible?")
    # tax_name_type: str | None = None


def bitfaktura_invoice_to_record(invoice: Invoice) -> TransactionRecord:
    return TransactionRecord(
        operation_datetime=invoice.created_at,  # 0
        bank_or_system="bitfaktura",  # 1
        account_name=None,  # 2
        account_number=invoice.seller_bank_account,  # 3
        transaction_type="invoice",  # 4
        account_currency_amount=invoice.price_gross,  # 5
        operation_currency_amount=invoice.price_gross,  # 6
        currency=invoice.currency,  # 7
        commission=None,  # 8
        balance_after_operation=None,  # 9
        operation_details=invoice.number,  # 10
        counterparty_details=invoice.buyer_name,  # 11
        counterparty_code=invoice.buyer_tax_no,  # 12
        counterparty_account_number=invoice.buyer_bank_account,  # 13
        mcc=None,  # 14
        comment=None,  # 15  FIXME: invoice.description ??
        transaction_id=str(invoice.id),  # 16
    )
