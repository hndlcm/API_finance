import json
import logging
import sys
from datetime import datetime, tzinfo
from logging.config import dictConfig
from pathlib import Path


def init_logging(
    folder: Path,
    file_name: str,
    config: Path,
    tz: tzinfo | None = None,
) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    with open(config, encoding="utf-8") as file:
        config_data = json.load(file)
        file_handler = config_data["handlers"]["FileHandler"]
        file_handler["filename"] = str(folder / file_name)
        dictConfig(config_data)

    if tz and sys.platform.startswith("win"):
        logging.Formatter.converter = lambda *args: datetime.now(
            tz
        ).timetuple()
