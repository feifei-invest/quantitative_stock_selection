import logging
import math
from datetime import datetime

import akshare as ak
import pandas as pd

from fetcher.base_fetcher import BaseFetcher
from fetcher.data_cache import DataCache
from config.settings import Settings
from common.models import DividendData

logger = logging.getLogger(__name__)


class HKDividendFetcher(BaseFetcher):
    def __init__(self, settings: Settings, cache: DataCache):
        super().__init__(settings)
        self.cache = cache

    def fetch(self, *args, **kwargs):
        pass

    def fetch_dividend_data(self, stock_code: str, latest_price: float = 0.0) -> DividendData:
        cache_key = f"hk_dividend_{stock_code}"
        cached = self.cache.get(cache_key)
        if cached:
            return DividendData(**cached)

        try:
            df = ak.stock_hk_dividend_detail(symbol=stock_code)
            self._rate_limit_pause()
        except Exception as e:
            logger.warning(f"获取港股{stock_code}分红数据失败: {e}")
            return DividendData()

        if df is None or df.empty:
            return DividendData()

        current_year = datetime.now().year
        recent_years = set(range(current_year - 3, current_year))

        total_dividend_per_share = 0.0
        dividend_years = set()

        for _, row in df.iterrows():
            try:
                date_val = row.get("除权除息日", row.get("公告日期", ""))
                if pd.isna(date_val):
                    continue
                year = int(str(date_val)[:4])
            except (ValueError, IndexError, TypeError):
                continue

            if year in recent_years:
                payout = self._safe_float(row, "派息")
                dividend_per_share = payout / 10.0
                total_dividend_per_share += dividend_per_share
                dividend_years.add(year)

        dividend_year_count = len(dividend_years)
        avg_dividend = total_dividend_per_share / 3.0
        dividend_yield = avg_dividend / latest_price if latest_price > 0 else 0.0

        result = DividendData(
            total_cash_dividend_3y=total_dividend_per_share,
            dividend_yield=dividend_yield,
            dividend_years=dividend_year_count,
        )
        self.cache.set(cache_key, {
            "total_cash_dividend_3y": result.total_cash_dividend_3y,
            "dividend_yield": result.dividend_yield,
            "dividend_years": result.dividend_years,
        })
        return result

    @staticmethod
    def _safe_float(row: pd.Series, col: str) -> float:
        try:
            val = row.get(col, 0)
            if val is None or (isinstance(val, float) and math.isnan(val)):
                return 0.0
            return float(val)
        except (ValueError, TypeError):
            return 0.0
