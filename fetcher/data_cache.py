import os
import json
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataCache:
    def __init__(self, cache_dir: str = "output_data/cache", expire_hours: int = 4):
        self.cache_dir = cache_dir
        self.default_expire_hours = expire_hours
        os.makedirs(cache_dir, exist_ok=True)

    def get(self, cache_key: str) -> dict | None:
        filepath = os.path.join(self.cache_dir, f"{cache_key}.json")
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if self._is_expired(cached):
                return None
            return cached.get("data")
        except (json.JSONDecodeError, KeyError):
            return None

    def set(self, cache_key: str, data: dict, expire_hours: int | None = None):
        filepath = os.path.join(self.cache_dir, f"{cache_key}.json")
        entry = {
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "expire_hours": expire_hours or self.default_expire_hours,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False, default=str)

    def is_expired(self, cache_key: str) -> bool:
        filepath = os.path.join(self.cache_dir, f"{cache_key}.json")
        if not os.path.exists(filepath):
            return True
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                cached = json.load(f)
            return self._is_expired(cached)
        except (json.JSONDecodeError, KeyError):
            return True

    def clear_all(self):
        if os.path.exists(self.cache_dir):
            for f in os.listdir(self.cache_dir):
                if f.endswith(".json"):
                    os.remove(os.path.join(self.cache_dir, f))

    def _is_expired(self, cached: dict) -> bool:
        try:
            ts = datetime.fromisoformat(cached["timestamp"])
            expire_hours = cached.get("expire_hours", self.default_expire_hours)
            elapsed = (datetime.now() - ts).total_seconds() / 3600
            return elapsed > expire_hours
        except (ValueError, TypeError):
            return True
