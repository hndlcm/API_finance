from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import BaseModel, BeforeValidator
from pydantic_settings import BaseSettings

TimeZone = Annotated[ZoneInfo, BeforeValidator(ZoneInfo)]


class LogSettings(BaseModel):
    directory: Path
    config: Path


class Settings(BaseSettings):
    log: LogSettings
    app_tz: TimeZone

    big_query_cred_file: Path
    big_query_table_id: str

    payment_config_file: Path

    flags: frozenset[str] = frozenset()

    # model_config = SettingsConfigDict(extra='allow')
