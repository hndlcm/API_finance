import logging

from google.cloud import bigquery
from google.oauth2 import service_account

from .bigquery_table import Table
from .payment_config import load_config
from .payments import (
    PortmoneScanner,
)
from .schemas import TransactionRecord
from .settings import Settings

logger = logging.getLogger(__name__)


def remove_duplicates(
    records: list[TransactionRecord]
) -> list[TransactionRecord]:
    records_map = {record.transaction_id: record for record in records}
    return list(records_map.values())


def scan_command(settings: Settings):
    logger.info("Loading payment config ...")

    payment_config = load_config(settings.payment_config_file)

    logger.info("Scanning payment systems ...")
    scanner_types = [
        PortmoneScanner,
        # PrivatScanner,
        # MonoScanner,
        # FacturowniaScanner,
        # BitfakturaScanner,
        # ERC20Scanner,
        # TRC20Scanner,
    ]
    transactions = []
    for ScannerType in scanner_types:
        if items := payment_config.root.get(ScannerType.KEY):
            try:
                scanner = ScannerType(items)
                records: list[TransactionRecord] = scanner.scan()
                transactions.extend(remove_duplicates(records))
            except Exception as e:
                logger.error("Error: %s %s", type(e), e)
                raise e

    if not transactions:
        logger.warning("No transactions.")
        return

    logger.info("Connecting to BigQuery ...")
    credentials = service_account.Credentials.from_service_account_file(
        str(settings.big_query_cred_file)
    )
    client = bigquery.Client(credentials.project_id, credentials)

    logger.info("Inserting and updating transactions in BigQuery table ...")
    table = Table(
        table_id=settings.big_query_table_id,
        pydantic_cls=TransactionRecord,
        primary_keys=["transaction_id", "bank_or_system"],
        client=client,
    )
    table.upsert_records(transactions)
