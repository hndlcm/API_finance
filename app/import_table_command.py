import json
import logging
from types import NoneType, UnionType  # noqa

from google.cloud import bigquery
from google.oauth2 import service_account

from .bigquery_table.table import Table
from .schemas import TransactionRecord
from .settings import Settings

logger = logging.getLogger(__name__)


def import_table_command(settings: Settings):
    credentials = service_account.Credentials.from_service_account_file(
        str(settings.big_query_cred_file)
    )
    client = bigquery.Client(
        credentials=credentials, project=credentials.project_id
    )
    logger.debug("Table: %s", settings.big_query_table_id)

    with open("app_data/_transactions.json", encoding="utf-8") as file:
        data = json.load(file)
        transactions = [
            TransactionRecord.model_validate(item) for item in data
        ]
        table = Table(
            table_id=settings.big_query_table_id,
            pydantic_cls=TransactionRecord,
            primary_keys=["transaction_id", "bank_or_system"],
            client=client,
        )
        table.insert_records(transactions)
