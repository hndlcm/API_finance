import time


class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        if max_calls <= 0 or period <= 0:
            raise ValueError("max_calls and period must be greater than 0")
        self._max_calls = max_calls
        self._period = period
        self._tokens = max_calls
        self._last_time = time.monotonic()

    def wait(self):
        now = time.monotonic()
        elapsed = now - self._last_time
        self._last_time = now
        self._tokens += elapsed * (self._max_calls / self._period)

        if self._tokens > self._max_calls:
            self._tokens = self._max_calls

        if self._tokens < 1:
            sleep_time = (1 - self._tokens) * (self._period / self._max_calls)
            time.sleep(sleep_time)
            self._tokens = 0
        else:
            self._tokens -= 1


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
