import json
import logging
from types import NoneType, UnionType  # noqa

from google.cloud import bigquery
from google.oauth2 import service_account

from .bigquery_table.table import Table
from .schemas import TransactionRecord
from .settings import Settings

logger = logging.getLogger(__name__)


def test_command(settings: Settings):
    with open("app_data/transactions.json", encoding="utf-8") as file:
        data = json.load(file)
        transactions = [
            TransactionRecord.model_validate(item) for item in data
        ]
    credentials = service_account.Credentials.from_service_account_file(
        str(settings.big_query_cred_file)
    )
    client = bigquery.Client(credentials.project_id, credentials)
    table = Table(
        table_id=settings.big_query_table_id,
        pydantic_cls=TransactionRecord,
        primary_keys=["transaction_id", "bank_or_system"],
        client=client,
    )
    table.upsert_records(transactions)
