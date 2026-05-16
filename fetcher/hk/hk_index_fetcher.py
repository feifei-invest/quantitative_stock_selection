import json
import logging
import os

import akshare as ak
import requests

from fetcher.base_fetcher import BaseFetcher
from fetcher.data_cache import DataCache
from config.settings import Settings
from common.models import StockInfo
from common.exceptions import DataFetchError

logger = logging.getLogger(__name__)

_EM_PUSH2_URL = "https://push2.eastmoney.com/api/qt/clist/get"
_EM_HK_FS = "m:128+t:3,m:128+t:4,m:128+t:5,m:128+t:6,m:128+t:7,m:128+t:8,m:128+t:9,m:128+t:10,m:128+t:11,m:128+t:12,m:128+t:13,m:128+t:14,m:128+t:15,m:128+t:16,m:128+t:17,m:128+t:18,m:128+t:19,m:128+t:20"
_LOCAL_LIST_FILE = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "hk_connect_constituents.json"))
_LOCAL_ALL_FILE = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "hk_all_stocks.json"))


class HKIndexFetcher(BaseFetcher):
    def __init__(self, settings: Settings, cache: DataCache):
        super().__init__(settings)
        self.cache = cache
        self.config = settings.hk_stock.constituents

    def fetch(self) -> list[StockInfo]:
        cache_key = "hk_connect_constituents"
        cached = self.cache.get(cache_key)
        if cached:
            return [StockInfo(**s) for s in cached]

        result = self._fetch_with_fallback()

        if self.config.max_stocks > 0 and len(result) > self.config.max_stocks:
            logger.info(f"港股列表截断: {len(result)}只 -> {self.config.max_stocks}只")
            result = result[:self.config.max_stocks]

        self.cache.set(
            cache_key,
            [{"code": s.code, "name": s.name, "exchange": s.exchange, "market": s.market} for s in result],
            expire_hours=4,
        )
        logger.info(f"获取港股通成分股: {len(result)}只")
        return result

    def _fetch_with_fallback(self) -> list[StockInfo]:
        errors = []

        for method_name, method in [
            ("em_push2", self._fetch_via_em_push2),
            ("akshare_ggt", self._fetch_via_akshare_ggt),
            ("sina_spot", self._fetch_via_sina_spot),
            ("local_list", self._fetch_via_local_list),
            ("local_all", self._fetch_via_local_all),
        ]:
            try:
                result = method()
                if result:
                    logger.info(f"[{method_name}] 获取港股列表成功: {len(result)}只")
                    return result
            except Exception as e:
                errors.append(f"{method_name}: {e}")
                logger.warning(f"[{method_name}] 获取失败: {e}")

        raise DataFetchError(
            data_type="hk_connect",
            message=f"所有数据源均失败: {'; '.join(errors)}"
        )

    def _fetch_via_em_push2(self) -> list[StockInfo]:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://quote.eastmoney.com/",
        })

        params = {
            "pn": 1, "pz": 1, "po": 1, "np": 1,
            "fltt": 2, "invt": 2, "fid": "f12",
            "fs": _EM_HK_FS,
            "fields": "f12,f14",
        }
        r = session.get(_EM_PUSH2_URL, params=params, timeout=20)
        data = r.json()
        total = data.get("data", {}).get("total", 0)
        if total == 0:
            return []

        all_results = []
        page_size = 500
        for page in range(1, (total // page_size) + 2):
            params["pn"] = page
            params["pz"] = page_size
            r = session.get(_EM_PUSH2_URL, params=params, timeout=20)
            page_data = r.json()
            items = page_data.get("data", {}).get("diff", [])
            if not items:
                break
            for item in items:
                code = str(item.get("f12", "")).zfill(5)
                name = str(item.get("f14", ""))
                all_results.append(StockInfo(code=code, name=name, exchange="HK", market="HK"))
            self._rate_limit_pause()

        return all_results

    def _fetch_via_akshare_ggt(self) -> list[StockInfo]:
        df = ak.stock_hk_ggt_components_em()
        self._rate_limit_pause()

        if df is None or df.empty:
            return []

        results = []
        for _, row in df.iterrows():
            code = str(row.get("港股代码", row.get("代码", ""))).zfill(5)
            name = str(row.get("港股简称", row.get("名称", "")))
            results.append(StockInfo(code=code, name=name, exchange="HK", market="HK"))
        return results

    def _fetch_via_sina_spot(self) -> list[StockInfo]:
        logger.info("使用新浪港股行情获取全部港股列表(作为港股通候选池)...")
        df = ak.stock_hk_spot()
        self._rate_limit_pause()

        if df is None or df.empty:
            return []

        results = []
        for _, row in df.iterrows():
            code = str(row.get("代码", "")).zfill(5)
            name = str(row.get("中文名称", ""))
            results.append(StockInfo(code=code, name=name, exchange="HK", market="HK"))
        return results

    def _fetch_via_local_file(self, file_path: str) -> list[StockInfo]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"本地文件不存在: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return [
            StockInfo(code=str(item.get("code", "")).zfill(5), name=item.get("name", ""), exchange="HK", market="HK")
            for item in data
        ]

    def _fetch_via_local_list(self) -> list[StockInfo]:
        return self._fetch_via_local_file(_LOCAL_LIST_FILE)

    def _fetch_via_local_all(self) -> list[StockInfo]:
        return self._fetch_via_local_file(_LOCAL_ALL_FILE)
