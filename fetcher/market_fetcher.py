import logging
import math
import time
from datetime import datetime

import akshare as ak
import pandas as pd
import requests

from fetcher.base_fetcher import BaseFetcher
from fetcher.data_cache import DataCache
from config.settings import Settings
from common.models import MarketData
from common.exceptions import DataFetchError

logger = logging.getLogger(__name__)


class MarketFetcher(BaseFetcher):
    def __init__(self, settings: Settings, cache: DataCache):
        super().__init__(settings)
        self.cache = cache

    def fetch(self, *args, **kwargs):
        pass

    def fetch_market_data(self, stock_code: str) -> MarketData:
        batch = self.fetch_batch_market_data([stock_code])
        return batch.get(stock_code, MarketData())

    def fetch_batch_market_data(self, stock_codes: list[str]) -> dict[str, MarketData]:
        cache_key = "all_market_data"
        cached = self.cache.get(cache_key)
        if cached:
            return {code: MarketData(**cached[code]) for code in stock_codes if code in cached}

        result_map = self._fetch_via_tencent(stock_codes)
        if not result_map:
            logger.warning("腾讯行情获取失败, 尝试akshare批量...")
            result_map = self._fetch_via_akshare_batch()

        if not result_map:
            raise DataFetchError(data_type="market_data", message="所有市值数据获取方式均失败")

        self.cache.set(cache_key, result_map, expire_hours=1)

        results = {}
        for code in stock_codes:
            if code in result_map:
                m = result_map[code]
                if m["total_market_cap"] <= 0:
                    logger.warning(f"股票{code}市值为0, 跳过")
                    continue
                results[code] = MarketData(**m)
        logger.info(f"批量获取市值数据: 请求{len(stock_codes)}只, 成功{len(results)}只")
        return results

    def _fetch_via_tencent(self, stock_codes: list[str]) -> dict:
        result_map = {}
        batch_size = 50
        for i in range(0, len(stock_codes), batch_size):
            batch = stock_codes[i:i + batch_size]
            code_strs = []
            for code in batch:
                prefix = "sh" if code.startswith("6") else "sz"
                code_strs.append(f"{prefix}{code}")

            try:
                url = f"http://qt.gtimg.cn/q={','.join(code_strs)}"
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()

                for line in resp.text.strip().split(";"):
                    line = line.strip()
                    if not line or '="' not in line:
                        continue
                    data_str = line.split('="')[1].rstrip('"')
                    fields = data_str.split("~")
                    if len(fields) < 46:
                        continue
                    code = fields[2]
                    try:
                        price = float(fields[3])
                        circ_mv_yi = float(fields[44])
                        total_mv_yi = float(fields[45])
                    except (ValueError, IndexError):
                        continue
                    result_map[code] = {
                        "total_market_cap": total_mv_yi * 1e8,
                        "circulating_market_cap": circ_mv_yi * 1e8,
                        "latest_price": price,
                    }
            except Exception as e:
                logger.warning(f"腾讯行情批次{i//batch_size+1}失败: {e}")

            time.sleep(0.5)

        logger.info(f"腾讯行情获取: {len(result_map)}只")
        return result_map

    def _fetch_via_akshare_batch(self) -> dict:
        result_map = {}
        for attempt in range(2):
            try:
                df = ak.stock_zh_a_spot_em()
                self._rate_limit_pause()
                for _, row in df.iterrows():
                    code = str(row.get("代码", "")).zfill(6)
                    result_map[code] = {
                        "total_market_cap": self._safe_float(row, "总市值"),
                        "circulating_market_cap": self._safe_float(row, "流通市值"),
                        "latest_price": self._safe_float(row, "最新价"),
                    }
                logger.info(f"akshare批量行情成功: {len(result_map)}只")
                return result_map
            except Exception as e:
                wait = 10 * (attempt + 1)
                logger.warning(f"akshare批量行情第{attempt+1}次失败: {e}, 等待{wait}秒...")
                time.sleep(wait)
        return {}

    @staticmethod
    def _safe_float(row: pd.Series, col: str) -> float:
        try:
            val = row.get(col, 0)
            if val is None or (isinstance(val, float) and math.isnan(val)):
                return 0.0
            return float(val)
        except (ValueError, TypeError):
            return 0.0
