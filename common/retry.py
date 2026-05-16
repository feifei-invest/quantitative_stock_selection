import time
import functools
import logging
from typing import Type, Tuple

from common.exceptions import DataFetchError, RateLimitError

logger = logging.getLogger(__name__)


def retry_on_failure(
    max_attempts: int = 3,
    interval_seconds: float = 5.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (DataFetchError, RateLimitError),
):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        wait_time = interval_seconds * (2 ** (attempt - 1))
                        logger.warning(
                            f"第{attempt}次重试失败: {e}, 等待{wait_time:.1f}秒后重试..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"达到最大重试次数{max_attempts}, 放弃: {e}")
                except Exception:
                    raise
            raise last_exception
        return wrapper
    return decorator
