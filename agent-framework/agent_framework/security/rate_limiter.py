import time
from typing import Any, Dict, Optional
from dataclasses import dataclass


class RateLimitError(Exception):
    def __init__(self, message: str, retry_after_seconds: float):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


@dataclass
class RateLimitConfig:
    rpm: int = 60
    tpm: int = 100000


class RateLimiter:
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._request_times: list = []
        self._token_counts: list = []
        self._lock = None

    def _now(self) -> float:
        return time.time()

    def _clean_window(self, window_seconds: float) -> None:
        now = self._now()
        self._request_times = [t for t in self._request_times if now - t < window_seconds]
        self._token_counts = [(t, c) for t, c in self._token_counts if now - t < window_seconds]

    def check_request(self, tokens: int = 0) -> None:
        self._clean_window(60.0)

        if len(self._request_times) >= self.config.rpm:
            oldest = self._request_times[0]
            retry_after = 60.0 - (self._now() - oldest)
            raise RateLimitError(
                f"Rate limit exceeded: {self.config.rpm} requests per minute",
                retry_after_seconds=max(retry_after, 0.1),
            )

        total_tokens = sum(c for _, c in self._token_counts) + tokens
        if total_tokens > self.config.tpm:
            if self._token_counts:
                oldest = self._token_counts[0][0]
                retry_after = 60.0 - (self._now() - oldest)
            else:
                retry_after = 60.0
            raise RateLimitError(
                f"Rate limit exceeded: {self.config.tpm} tokens per minute",
                retry_after_seconds=max(retry_after, 0.1),
            )

    def record_request(self, tokens: int = 0) -> None:
        now = self._now()
        self._request_times.append(now)
        if tokens > 0:
            self._token_counts.append((now, tokens))
