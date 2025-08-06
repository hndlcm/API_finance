import asyncio
import logging
import time
from collections.abc import AsyncIterator
from functools import wraps
from typing import TypeAlias

ExceptionTypes: TypeAlias = (
    type[BaseException] | tuple[type[BaseException], ...]  # type: ignore
)
Delays = tuple[float, ...]

_logger = logging.getLogger(__name__)


class SyncAttempt:
    def __init__(self, context: "RetryContext"):
        self._context = context

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, _tb):
        if exc_type is None or not isinstance(exc_val, self._context.on):
            return False

        if (delay := self._context.get_dalay()) is None:
            return False

        self._context.log(exc_val, delay)
        time.sleep(delay)
        return True


class AsyncAttempt:
    def __init__(self, context: "RetryContext"):
        self._context = context

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, tb):
        if exc_type is None or not isinstance(exc_val, self._context.on):
            return False

        if (delay := self._context.get_dalay()) is None:
            return False

        self._context.log(exc_val, delay)

        await asyncio.sleep(delay)
        return True


class RetryContext:
    def __init__(
        self,
        name: str,
        logger: logging.Logger,
        on: ExceptionTypes,
        delays: Delays,
    ):
        self._logger = logger
        self._on = on
        self._name = name
        self._delays = delays
        self._index = 0
        self._attempts = (
            len(self._delays) - 1 if self._infinite() else len(self._delays)
        )

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def on(self) -> ExceptionTypes:
        return self._on

    @property
    def name(self) -> str:
        return self._name

    def __iter__(self) -> AsyncIterator[AsyncAttempt]:
        return self

    def __next__(self) -> SyncAttempt:
        return SyncAttempt(self)

    def __aiter__(self) -> AsyncIterator[AsyncAttempt]:
        return self

    async def __anext__(self) -> AsyncAttempt:
        return AsyncAttempt(self)

    def _infinite(self):
        return self._delays and self._delays[-1] is Ellipsis

    def copy(self) -> "RetryContext":
        return RetryContext(self._name, self._logger, self._on, self._delays)

    def __copy__(self) -> "RetryContext":
        return self.copy()

    def get_dalay(self) -> float | None:
        if self._index < self._attempts:
            delay = self._delays[self._index]
            self._index += 1
        elif self._infinite():
            delay = self._delays[-2]
        else:
            return None
        return delay

    def log(self, exc_val, delay) -> None:
        self._logger.warning(
            '%s failed with %s: "%s". Retrying after %ss.',
            self._name,
            type(exc_val),
            exc_val,
            delay,
        )

    def reset(self):
        self._index = 0


def retry(
    logger_: logging.Logger,
    on: ExceptionTypes,
    delays: Delays,
):
    def decorator(func):
        context = RetryContext(func.__name__, logger_, on, delays)

        if not asyncio.iscoroutinefunction(func):

            @wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in context.copy():
                    with attempt:
                        return func(*args, **kwargs)
        else:

            @wraps(func)
            async def wrapper(*args, **kwargs):
                async for attempt in context.copy():
                    async with attempt:
                        return await func(*args, **kwargs)

        return wrapper

    return decorator
