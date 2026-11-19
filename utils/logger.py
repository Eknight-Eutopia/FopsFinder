import logging
import os
from copy import copy
from typing import ClassVar

from config.config import config

log_level = {
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

level = log_level[config["misc"]["log_level"].upper()]


class CustomFormatter(logging.Formatter):
    """Local timestamps and subdued metadata; severity colors never reach the body."""

    default_msec_format = "%s.%03d"
    _DIM = "\x1b[90m"
    _RESET = "\x1b[0m"
    _LEVEL_COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: "\x1b[36m",
        logging.INFO: "\x1b[32m",
        logging.WARNING: "\x1b[33m",
        logging.ERROR: "\x1b[31m",
        logging.CRITICAL: "\x1b[1;31m",
    }

    def __init__(self, *, color: bool = False) -> None:
        super().__init__("%(asctime)s %(levelname)-7s %(name)s: %(message)s")
        self.color = color

    def format(self, record: logging.LogRecord) -> str:
        # A different handler may render the same record as plain text.
        return super().format(copy(record))

    def formatMessage(self, record: logging.LogRecord) -> str:
        if not self.color:
            return super().formatMessage(record)
        severity_color = self._LEVEL_COLORS.get(record.levelno, "")
        padding = " " * max(0, 7 - len(record.levelname))
        return (
            f"{self._DIM}{record.asctime}{self._RESET} "
            f"{severity_color}{record.levelname}{self._RESET}{padding} "
            f"{self._DIM}{record.name}{self._RESET}: {record.message}"
        )


def _create_console_handler(handler_level):
    console_handler = logging.StreamHandler()
    console_handler.setLevel(handler_level)
    console_handler.setFormatter(
        CustomFormatter(
            color=(
                console_handler.stream.isatty()
                and "NO_COLOR" not in os.environ
                and os.environ.get("TERM") != "dumb"
            ),
        )
    )
    return console_handler


root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)
if not root_logger.handlers:
    root_logger.addHandler(_create_console_handler(logging.WARNING))
else:
    for handler in root_logger.handlers:
        handler.setLevel(max(handler.level, logging.WARNING))


def get_logger(name=__name__):
    logger = logging.getLogger(f"LKMAgent.{name}")
    logger.setLevel(level)
    logger.propagate = False
    if not logger.handlers:
        logger.addHandler(_create_console_handler(level))
    return logger
