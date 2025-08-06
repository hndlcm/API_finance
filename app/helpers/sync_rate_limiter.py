import time
from collections import deque


class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        if max_calls <= 0 or period <= 0:
            raise ValueError("max_calls and period must be greater than 0")
        self._max_calls = max_calls
        self._period = period
        self._calls: deque[int] = deque()

    def wait(self):
        now = time.monotonic()
        while self._calls and self._calls[0] <= now - self._period:
            self._calls.popleft()

        if len(self._calls) >= self._max_calls:
            sleep_time = self._calls[0] + self._period - now
            time.sleep(sleep_time)
            now = time.monotonic()
            while self._calls and self._calls[0] <= now - self._period:
                self._calls.popleft()

        self._calls.append(time.monotonic())


if __name__ == "__main__":
    limiter = RateLimiter(max_calls=2, period=1)

    for _ in range(10):
        start = time.monotonic()
        limiter.wait()

        # random_delay = random.uniform(0, 0.2)
        # print(f"{random_delay=}")
        # time.sleep(random_delay)

        end = time.monotonic()
        ellpsed = end - start
        print(f"{ellpsed=}")
