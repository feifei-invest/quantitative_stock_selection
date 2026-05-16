import time
import logging
from abc import ABC, abstractmethod
from typing import Any

from config.settings import Settings
from common.exceptions import DataMissingError
from common.retry import retry_on_failure

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    def __init__(self, settings: Settings):
        self.settings = settings
        self._request_interval = 0.2

    @abstractmethod
    def fetch(self, *args, **kwargs) -> Any:
        pass

    def fetch_with_retry(self, *args, **kwargs) -> Any:
        retry_cfg = self.settings.data_source
        decorated = retry_on_failure(
            max_attempts=retry_cfg.max_attempts,
            interval_seconds=retry_cfg.interval_seconds,
        )(self.fetch)
        return decorated(*args, **kwargs)

    def _handle_data_missing(self, stock_code: str, field: str):
        raise DataMissingError(stock_code=stock_code, missing_fields=[field])

    def _validate_data(self, data: dict, required_fields: list, stock_code: str) -> dict:
        missing = [f for f in required_fields if f not in data or data[f] is None]
        if missing:
            raise DataMissingError(stock_code=stock_code, missing_fields=missing)
        return data

    def _rate_limit_pause(self):
        time.sleep(self._request_interval)
