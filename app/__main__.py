import argparse
import enum
import logging
import sys
from pathlib import Path

import colorama
from pydantic import ValidationError

from .helpers.logging_utils import init_logging
from .scan_command import scan_command
from .settings import Settings

logger = logging.getLogger(Path(__file__).parent.name)


class Commands(enum.StrEnum):
    SCAN = enum.auto()


def main():
    colorama.init()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="Path to the environment variables file",
    )
    subparsers = parser.add_subparsers(dest="command", required=False)
    subparsers.add_parser(str(Commands.SCAN.value), help="Scan finance")
    args = parser.parse_args()
    try:
        settings = Settings(
            _env_file=args.env_file,  # noqa
            _env_nested_delimiter="__",  # noqa
        )
    except ValidationError as e:
        from_ = args.env_file if args.env_file else "system environment"
        error_text = f"Error occurred while loading settings from {from_}\n{e}"
        print(error_text, file=sys.stderr)
        return 1

    init_logging(
        settings.log.directory,
        settings.log.config,
        settings.app_tz,
        filename=args.command + ".txt" if args.command else "log.txt",
        flags=settings.flags,
    )
    logger.debug("Command=%s Settings=%s", args.command, settings)
    try:
        match args.command:
            case Commands.SCAN:
                scan_command(settings)
            case _:
                scan_command(settings)
        return 0
    except KeyboardInterrupt:
        logger.warning("Program execution interrupted by the user.")
        return 0
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception(e)
        return 1


main()
