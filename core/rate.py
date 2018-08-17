import asyncio
import time


class TokenLimiter:
    Seconds = 1

    def __init__(self, rate, unit_of_time=Seconds):
        if rate <= 0:
            raise ValueError('rate should be greater than zero')
        if unit_of_time <= 0:
            raise ValueError('unit_of_time should be greater than zero')

        self._u = int(unit_of_time)
        self._rate = self._t = self._capacity = float(rate)

        self._lc = time.monotonic()

        self._lock = asyncio.Lock()

    async def consume(self, consume=1, block=True):
        if consume <= 0:
            raise ValueError('consume should be greater than zero')

        while True:
            async with self._lock:
                self._refill()

                if consume <= self._t:
                    self._t -= consume
                    return

                sleep_time = self._u * (consume - self._t) / self._rate

            if block:
                await asyncio.sleep(sleep_time)
                continue

            return sleep_time

    def _refill(self):
        t = time.monotonic()
        delta = t - self._lc
        self._t = min(self._capacity, self._t + self._rate * delta / self._u)
        self._lc = t
