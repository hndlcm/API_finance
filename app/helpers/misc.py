from datetime import datetime, timedelta
from typing import Iterator


def datetime_range_gen(
    start_date: datetime,
    end_date: datetime,
    delta: timedelta,
) -> Iterator[tuple[datetime, datetime]]:
    start = start_date
    while start < end_date:
        end = min(start + delta, end_date)
        yield start, end
        start = end
