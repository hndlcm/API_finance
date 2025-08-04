import enum
import logging
from datetime import datetime
from decimal import Decimal
from types import NoneType, UnionType  # noqa
from typing import Any, Final, Type, get_args, get_origin

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

SPECIAL_CHARS: Final[dict] = {
    "\\": "\\\\",
    "'": '"',
    "\n": " ",
    "\r": " ",
    "\t": " ",
}


def escape_string(value: str | None) -> str:
    if value is None:
        return "NULL"

    for src, replacement in SPECIAL_CHARS.items():
        value = value.replace(src, replacement)

    # value = "".join(ch for ch in value if ord(ch) >= 0x20)
    return f"'{value}'"


def wrap_name(name: str) -> str:
    return f"`{name}`"  # noqa: W604


def wrap_value(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, Decimal):
        return f"CAST('{value}' AS NUMERIC)"
    if isinstance(value, datetime):
        dt_str = value.strftime("%Y-%m-%d %H:%M:%S")
        return f"TIMESTAMP('{dt_str} UTC')"
    if isinstance(value, int) or isinstance(value, float):
        return str(value)
    return escape_string(value)


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


def _build_values_sql(records: list[BaseModel], columns: list[str]) -> str:
    lines = []
    for record in records:
        row_values = []
        for column in columns:
            value = getattr(record, column)
            row_values.append(wrap_value(value))
        lines.append("(" + ",".join(row_values) + ")")

    return ",\n".join(lines)


def build_insert_query(table_id: str, records: list[BaseModel]) -> str | None:
    if not records:
        return None

    cls = type(records[0])
    columns = list(cls.model_fields.keys())

    cols_sql = ", ".join(wrap_name(column_name) for column_name in columns)
    values_sql = _build_values_sql(records, columns)
    query = (
        f"INSERT INTO {wrap_name(table_id)} ({cols_sql})\n"
        f"VALUES\n{values_sql};"  # noqa: E231, E702
    )
    logger.debug("insert query:\n%s", query)
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
    logger.debug("merge query:\n%s", query)
    return query
