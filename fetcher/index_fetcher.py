import logging

import akshare as ak

from fetcher.base_fetcher import BaseFetcher
from fetcher.data_cache import DataCache
from config.settings import Settings
from common.models import StockInfo
from common.exceptions import DataFetchError

logger = logging.getLogger(__name__)


class IndexFetcher(BaseFetcher):
    def __init__(self, settings: Settings, cache: DataCache):
        super().__init__(settings)
        self.cache = cache

    def fetch(self) -> list[StockInfo]:
        cache_key = "hs300_constituents"
        cached = self.cache.get(cache_key)
        if cached:
            return [StockInfo(**s) for s in cached]

        try:
            df = ak.index_stock_cons_csindex(symbol="000300")
            self._rate_limit_pause()
        except Exception as e:
            raise DataFetchError(data_type="hs300_constituents", message=str(e))

        results = []
        for _, row in df.iterrows():
            code = str(row.get("成分券代码", "")).zfill(6)
            name = str(row.get("成分券名称", ""))
            exchange = "SH" if code.startswith("6") else "SZ"
            results.append(StockInfo(code=code, name=name, exchange=exchange))

        results.sort(key=lambda x: x.code)
        self.cache.set(cache_key, [{"code": s.code, "name": s.name, "exchange": s.exchange} for s in results], expire_hours=1)
        logger.info(f"获取沪深300成分股: {len(results)}只")
        return results
