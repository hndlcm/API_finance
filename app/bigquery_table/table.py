import itertools
import logging
from types import NoneType, UnionType  # noqa
from typing import Final, Type

from google.cloud import bigquery
from pydantic import BaseModel

from .qp import insert_records
from .utils import build_insert_query, build_merge_query, generate_schema

logger = logging.getLogger(__name__)

BATCH_SIZE: Final[int] = 10


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
        self._fields = list(pydantic_cls.model_fields.keys())

    def recreate(self) -> bigquery.Table:
        table = bigquery.Table(
            self._table_id,  # type: ignore
            schema=self._schema,
        )
        self._client.delete_table(table, not_found_ok=True)
        table = self._client.create_table(table, exists_ok=True)
        return table

    def insert_records(self, records: list[BaseModel]) -> None:
        query = build_insert_query(self._table_id, records)
        query_job: bigquery.job.QueryJob = self._client.query(query)
        query_job.result()

    def _create_temp_table(
        self,
        temp_table_id: str,
        records: list[BaseModel],
    ) -> bigquery.Table:
        table = bigquery.Table(
            temp_table_id,  # type: ignore
            schema=self._schema,
        )
        self._client.create_table(table, exists_ok=True)
        # i = 0
        for batch in itertools.batched(records, BATCH_SIZE):  # type: ignore
            insert_records(self._client, temp_table_id, batch)
            break
            # query_job: bigquery.job.QueryJob = self._client.query(query)
            # query_job.result()
            # logger.debug("Inserted batch %i...%d", i, len(batch))
            # i += len(batch)
        return table

    def upsert_records(self, records: list[BaseModel]) -> None:
        temp_table_id = f"{self._table_id}_temp"
        self._client.delete_table(temp_table_id, not_found_ok=True)
        self._create_temp_table(temp_table_id, records)
        try:
            merge_query = build_merge_query(
                self._table_id,
                temp_table_id,
                self._primary_keys,
                self._fields,
            )
            query_job: bigquery.job.QueryJob = self._client.query(merge_query)
            query_job.result()
        finally:
            self._client.delete_table(temp_table_id, not_found_ok=True)
