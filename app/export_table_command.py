import json
import logging

from google.cloud import bigquery
from google.oauth2 import service_account

from .schemas import TransactionRecord
from .settings import Settings

logger = logging.getLogger(__name__)


def export_table_command(settings: Settings):
    credentials = service_account.Credentials.from_service_account_file(
        str(settings.big_query_cred_file)
    )
    big_query_client = bigquery.Client(
        credentials=credentials, project=credentials.project_id
    )
    logger.debug("Table: %s", settings.big_query_table_id)

    query = f"SELECT * FROM `{settings.big_query_table_id}`"
    query_job = big_query_client.query(query)
    results = query_job.result()
    records = []
    for row in results:
        record = TransactionRecord.model_validate(dict(row))
        records.append(record)

    with open("app_data/transactions_export.json", "w", encoding="utf-8") as f:
        data = [record.model_dump() for record in records]
        json.dump(data, f, indent=4, ensure_ascii=False, default=str)
