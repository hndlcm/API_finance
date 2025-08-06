import logging

from google.cloud import bigquery
from google.oauth2 import service_account

from .bigquery_table.table import Table
from .schemas import TransactionRecord
from .settings import Settings

logger = logging.getLogger(__name__)


def recreate_table_command(settings: Settings):
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
    table.recreate()
