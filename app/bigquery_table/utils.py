import enum
import logging
from datetime import datetime
from decimal import Decimal
from types import NoneType, UnionType  # noqa
from typing import Final, Type, get_args, get_origin

from google.cloud import bigquery
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Mode(enum.StrEnum):
    NULLABLE = "NULLABLE"
    REQUIRED = "REQUIRED"


class WriteDisposition(enum.StrEnum):
    WRITE_TRUNCATE = "WRITE_TRUNCATE"
    WRITE_APPEND = "WRITE_APPEND"
    WRITE_EMPTY = "WRITE_EMPTY"


PYTHON_TO_BIGQUERY_TYPE_MAP: Final[dict] = {
    str: "STRING",
    int: "INT64",
    Decimal: "NUMERIC",
    datetime: "TIMESTAMP",
}


def wrap_name(name: str) -> str:
    return f"`{name}`"  # noqa: W604


def get_database_type(field_name, field_info) -> str:
    annotation = field_info.annotation
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is None or len(args) == 0:
        python_type = annotation
    elif origin is UnionType and len(args) == 2 and NoneType in args:
        python_type = next(arg for arg in args if arg is not NoneType)
    else:
        python_type = None

    bq_type = PYTHON_TO_BIGQUERY_TYPE_MAP.get(python_type)

    if python_type is None or bq_type is None:
        raise TypeError(
            f"Unsupported type: {annotation} " f"for field {field_name}"
        )
    return bq_type


# SCHEMA


def generate_schema(cls: Type[BaseModel]) -> list[bigquery.SchemaField]:
    schema = []
    for field_name, field_info in cls.model_fields.items():
        annotation = field_info.annotation
        origin = get_origin(annotation)
        args = get_args(annotation)
        if origin is None or len(args) == 0:
            python_type = annotation
            mode = Mode.REQUIRED
        elif origin is UnionType and len(args) == 2 and NoneType in args:
            python_type = next(arg for arg in args if arg is not NoneType)
            mode = Mode.NULLABLE
        else:
            raise TypeError(
                f"Unsupported type: {annotation} for field {field_name}"
            )
        bq_type = PYTHON_TO_BIGQUERY_TYPE_MAP.get(python_type)
        if not bq_type:
            raise TypeError(
                f"Unsupported type: {python_type} for field {field_name}"
            )
        schema.append(bigquery.SchemaField(field_name, bq_type, mode=mode))
    return schema


# INSERT


def build_insert_query(
    table_id: str,
    column_names: list[str],
    placeholders: list[str],
):
    placeholders_sql = ",\n".join(placeholders)
    query = (
        f"INSERT INTO {wrap_name(table_id)}\n"
        f"({', '.join(wrap_name(c) for c in column_names)})\n"
        f"VALUES\n"
        f"{placeholders_sql}"
    )
    return query


# MERGE


def build_merge_query(
    table_id: str,
    temp_table_id: str,
    primary_keys: list[str],
    update_fields: list[str],
) -> str:
    on_conditions = " AND ".join(
        [f"T.{key} = S.{key}" for key in primary_keys]
    )
    update_set = ",\n        ".join(
        [
            f"T.{field} = S.{field}"
            for field in update_fields
            if field not in primary_keys
        ]
    )
    insert_columns = ", ".join(
        primary_keys + [f for f in update_fields if f not in primary_keys]
    )
    insert_values = ", ".join(
        [
            f"S.{field}"
            for field in primary_keys
            + [f for f in update_fields if f not in primary_keys]
        ]
    )
    query = (
        f"MERGE {wrap_name(table_id)} T\n"
        f"USING {wrap_name(temp_table_id)} S\n"
        f"ON {on_conditions}\n"
        f"WHEN MATCHED THEN\n"
        f"UPDATE SET {update_set}\n"
        f"WHEN NOT MATCHED THEN\n"
        f"INSERT ({insert_columns})\n"
        f"VALUES ({insert_values});"  # noqa: E231, E702
    )
    return query
