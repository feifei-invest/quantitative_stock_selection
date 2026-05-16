import logging
import math
import time

import requests

from fetcher.base_fetcher import BaseFetcher
from fetcher.data_cache import DataCache
from config.settings import Settings
from common.models import MarketData
from common.exceptions import DataFetchError

logger = logging.getLogger(__name__)


class HKMarketFetcher(BaseFetcher):
    def __init__(self, settings: Settings, cache: DataCache):
        super().__init__(settings)
        self.cache = cache

    def fetch(self, *args, **kwargs):
        pass

    def fetch_batch_market_data(self, stock_codes: list[str]) -> dict[str, MarketData]:
        cache_key = "hk_all_market_data"
        cached = self.cache.get(cache_key)
        if cached:
            return {code: MarketData(**cached[code]) for code in stock_codes if code in cached}

        result_map = self._fetch_via_tencent(stock_codes)

        if not result_map:
            result_map = self._fetch_via_akshare(stock_codes)

        if not result_map:
            raise DataFetchError(data_type="hk_market_data", message="港股市值数据获取失败")

        self.cache.set(cache_key, result_map, expire_hours=1)

        results = {}
        for code in stock_codes:
            if code in result_map:
                m = result_map[code]
                if m["total_market_cap"] <= 0:
                    logger.warning(f"港股{code}市值为0, 跳过")
                    continue
                results[code] = MarketData(**m)
        logger.info(f"港股市值获取: 请求{len(stock_codes)}只, 成功{len(results)}只")
        return results

    def _fetch_via_tencent(self, stock_codes: list[str]) -> dict:
        result_map = {}
        batch_size = 50
        for i in range(0, len(stock_codes), batch_size):
            batch = stock_codes[i:i + batch_size]
            code_strs = [f"hk{code}" for code in batch]

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
                    code = fields[2].zfill(5)
                    try:
                        price = float(fields[3])
                        total_mv_yi = float(fields[45])
                        circ_mv_yi = float(fields[44])
                    except (ValueError, IndexError):
                        continue
                    result_map[code] = {
                        "total_market_cap": total_mv_yi * 1e8,
                        "circulating_market_cap": circ_mv_yi * 1e8,
                        "latest_price": price,
                    }
            except Exception as e:
                logger.warning(f"港股腾讯行情批次{i//batch_size+1}失败: {e}")
            time.sleep(0.5)

        logger.info(f"港股腾讯行情: {len(result_map)}只")
        return result_map

    def _fetch_via_akshare(self, stock_codes: list[str]) -> dict:
        import akshare as ak
        result_map = {}
        try:
            df = ak.stock_hk_spot_em()
            self._rate_limit_pause()
            for _, row in df.iterrows():
                code = str(row.get("代码", "")).zfill(5)
                total_mv = self._safe_float(row, "总市值")
                circ_mv = self._safe_float(row, "流通市值")
                price = self._safe_float(row, "最新价")
                result_map[code] = {
                    "total_market_cap": total_mv,
                    "circulating_market_cap": circ_mv,
                    "latest_price": price,
                }
        except Exception as e:
            logger.warning(f"akshare港股行情失败: {e}")
        return result_map

    @staticmethod
    def _safe_float(row, col: str) -> float:
        try:
            val = row.get(col, 0)
            if val is None or (isinstance(val, float) and math.isnan(val)):
                return 0.0
            return float(val)
        except (ValueError, TypeError):
            return 0.0
