import time


class ElapsedTimer:
    def __init__(self):
        self._start = None
        self._end = None

    def start(self):
        self._start = time.monotonic()
        self._end = None

    def stop(self):
        if self._start is None:
            raise RuntimeError("Timer was not started")
        self._end = time.monotonic()

    def elapsed(self) -> float | None:
        if self._start is None:
            return None
        if self._end is not None:
            return self._end - self._start
        return time.monotonic() - self._start

    def reset(self):
        self._start = None
        self._end = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


if __name__ == "__main__":
    with ElapsedTimer() as t:
        time.sleep(1)

    print(t.elapsed())
