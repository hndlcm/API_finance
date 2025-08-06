import json
import logging
from datetime import datetime, tzinfo
from logging.config import dictConfig
from pathlib import Path


def init_logging(
    folder: Path,
    config: Path,
    tz: tzinfo | None = None,
    filename: str = "log.txt",
    flags: frozenset[str] = frozenset(),
) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    with open(config, encoding="utf-8") as file:
        config_data = json.load(file)
        file_handler = config_data["handlers"]["FileHandler"]
        file_handler["filename"] = str(folder / filename)
        dictConfig(config_data)

    if tz:
        logging.Formatter.converter = lambda *args: datetime.now(
            tz
        ).timetuple()
