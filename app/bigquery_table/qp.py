import logging
from datetime import datetime
from decimal import Decimal

from google.cloud import bigquery
from google.cloud.bigquery import ScalarQueryParameter
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def get_bq_type(py_type):
    if py_type is str:
        return "STRING"
    if py_type is int:
        return "INT64"
    if py_type is float:
        return "FLOAT64"
    if py_type is Decimal:
        return "NUMERIC"
    if py_type is datetime:
        return "TIMESTAMP"
    raise TypeError(f"Unsupported type: {py_type}")


def insert_records(
    client: bigquery.Client, table: str, records: list[BaseModel]
):
    columns = list(BaseModel.model_fields.keys())
    placeholders = []
    parameters = []
    param_index = 0

    for record in records:
        row_placeholders = []
        for col_name in columns:
            value = getattr(record, col_name)
            param_name = f"param_{param_index}"
            param_index += 1

            if value is None:
                row_placeholders.append("NULL")
            else:
                field_info = BaseModel.model_fields[col_name]
                bq_type = get_bq_type(
                    field_info.annotation
                    if getattr(field_info.annotation, "__origin__", None)
                    is not None
                    else field_info.annotation
                )
                parameters.append(
                    ScalarQueryParameter(param_name, bq_type, value)
                )
                row_placeholders.append(f"@{param_name}")

        placeholders.append(f"({', '.join(row_placeholders)})")

    query = f"""
        INSERT INTO `{table}` ({', '.join(f'`{c}`' for c in columns)})
        VALUES
        ({',\n'.join(placeholders)})
    """
    logger.debug(query)

    job_config = bigquery.QueryJobConfig(query_parameters=parameters)
    query_job = client.query(query, job_config=job_config)
    query_job.result()
