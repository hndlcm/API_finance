import argparse
import enum
import logging
import sys
from pathlib import Path

import colorama
from pydantic import ValidationError

from .export_table_command import export_table_command
from .helpers.logging_utils import init_logging
from .import_table_command import import_table_command
from .recreate_table_command import recreate_table_command
from .scan_command import scan_command, scan_once_command
from .settings import Settings

logger = logging.getLogger(Path(__file__).parent.name)


class Commands(enum.StrEnum):
    SCAN = enum.auto()
    SCAN_ONCE = enum.auto()
    RECREATE_TABLE = enum.auto()
    IMPORT_TABLE = enum.auto()
    EXPORT_TABLE = enum.auto()


def main():
    colorama.init()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="Path to the environment variables file",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        str(Commands.SCAN.value), help="Scan finance on schedule"
    )
    subparsers.add_parser(
        str(Commands.SCAN_ONCE.value),
        help="Scan finance once",
    )
    subparsers.add_parser(
        str(Commands.RECREATE_TABLE.value),
        help="Recreate bigquery table",
    )
    subparsers.add_parser(
        str(Commands.IMPORT_TABLE.value),
        help="Import data from csv to bigquery table",
    )
    subparsers.add_parser(
        str(Commands.EXPORT_TABLE.value),
        help="Export data from bigquery table to csv",
    )

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
    )
    logger.info("Command=%s Settings=%s", args.command, settings)
    try:
        match args.command:
            case Commands.SCAN_ONCE:
                scan_once_command(settings)
            case Commands.SCAN:
                scan_command(settings)
            case Commands.RECREATE_TABLE:
                recreate_table_command(settings)
            case Commands.IMPORT_TABLE:
                import_table_command(settings)
            case Commands.EXPORT_TABLE:
                export_table_command(settings)
        return 0
    except KeyboardInterrupt:
        logger.warning("Program execution interrupted by the user.")
        return 0
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception(e)
        return 1


main()
