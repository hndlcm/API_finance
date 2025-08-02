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
    rate_limit: tuple[float, float]

    big_query_cred_file: Path = Path(
        "app_data/fin-api-463108-7083ad9de650.json"
    )

    payment_config_file: Path = Path("app_data/config.json")

    flags: frozenset[str] = frozenset()

    # model_config = SettingsConfigDict(extra='allow')
