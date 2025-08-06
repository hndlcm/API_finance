import itertools
import logging
from typing import Final, Iterable, Sequence, Type

from google.cloud import bigquery
from google.cloud.bigquery import ScalarQueryParameter
from pydantic import BaseModel

from .utils import (
    build_insert_query,
    build_merge_query,
    generate_schema,
    get_database_type,
)

logger = logging.getLogger(__name__)

BATCH_SIZE: Final[int] = 500


class Table:
    def __init__(
        self,
        table_id: str,
        pydantic_cls: Type[BaseModel],
        primary_keys: list[str],
        client: bigquery.Client,
    ):
        self._table_id = table_id
        self._pydantic_cls = pydantic_cls
        self._primary_keys = primary_keys
        self._client = client
        self._schema = generate_schema(self._pydantic_cls)
        self._field_names = list(pydantic_cls.model_fields.keys())

    def recreate(self) -> bigquery.Table:
        table = bigquery.Table(
            self._table_id,  # type: ignore
            schema=self._schema,
        )
        self._client.delete_table(table, not_found_ok=True)
        table = self._client.create_table(table, exists_ok=True)
        return table

    def _insert_records_to_table(
        self, table_id: str, records: Iterable[BaseModel]
    ) -> None:
        parameters = []
        placeholders = []

        parameter_index = 0
        for record in records:
            record_placeholders = []
            for field_name, field_info in record.model_fields.items():
                value = getattr(record, field_name, None)
                bq_type = get_database_type(field_name, field_info)
                parameter_name = f"param_{parameter_index}"
                record_placeholders.append(f"@{parameter_name}")
                parameter = ScalarQueryParameter(
                    parameter_name, bq_type, value
                )
                parameters.append(parameter)
                parameter_index += 1
            placeholders.append(f"({', '.join(record_placeholders)})")

        query = build_insert_query(table_id, self._field_names, placeholders)
        job_config = bigquery.QueryJobConfig(query_parameters=parameters)
        query_job = self._client.query(query, job_config=job_config)
        query_job.result()

    def insert_records(self, records: Sequence[BaseModel]) -> None:
        i = 0
        for batch in itertools.batched(records, BATCH_SIZE):  # type: ignore
            self._insert_records_to_table(self._table_id, batch)
            logger.debug("Batch %d..%d has been inserted", i, i + len(batch))
            i += len(batch)

    def _create_temp_table(
        self,
        temp_table_id: str,
        records: Sequence[BaseModel],
    ) -> bigquery.Table:
        table = bigquery.Table(
            temp_table_id,  # type: ignore
            schema=self._schema,
        )
        self._client.create_table(table, exists_ok=True)
        i = 0
        for batch in itertools.batched(records, BATCH_SIZE):  # type: ignore
            self._insert_records_to_table(temp_table_id, batch)
            logger.debug("Batch %d..%d has been inserted", i, i + len(batch))
            i += len(batch)
        return table

    def upsert_records(self, records: Sequence[BaseModel]) -> None:
        temp_table_id = f"{self._table_id}_temp"
        self._client.delete_table(temp_table_id, not_found_ok=True)
        self._create_temp_table(temp_table_id, records)
        try:
            merge_query = build_merge_query(
                self._table_id,
                temp_table_id,
                self._primary_keys,
                self._field_names,
            )
            query_job: bigquery.job.QueryJob = self._client.query(merge_query)
            query_job.result()
        finally:
            self._client.delete_table(temp_table_id, not_found_ok=True)
