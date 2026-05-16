import logging
import math

import akshare as ak
import pandas as pd

from fetcher.base_fetcher import BaseFetcher
from fetcher.data_cache import DataCache
from config.settings import Settings
from common.models import BalanceSheet, IncomeStatement, CashFlowStatement
from common.exceptions import DataFetchError, DataMissingError

logger = logging.getLogger(__name__)

_BS_ITEM_MAP = {
    "cash_and_equivalents": ["004002010", "004002011"],
    "total_current_assets": ["004002999"],
    "total_assets": ["004009999"],
    "total_current_liabilities": ["004011999"],
    "total_liabilities": ["004025999"],
    "net_assets": ["004028999"],
}

_BS_DEBT_ITEMS = ["004011010", "004020001"]

_INC_ITEM_MAP = {
    "revenue": ["004001999"],
    "operating_cost": ["004005001"],
    "net_profit": ["004012999"],
    "deducted_net_profit": ["004025002"],
}

_CF_ITEM_MAP = {
    "operating_cash_flow": ["003999"],
    "capital_expenditure": ["005005", "005007"],
}


class HKFinanceFetcher(BaseFetcher):
    def __init__(self, settings: Settings, cache: DataCache):
        super().__init__(settings)
        self.cache = cache

    def fetch(self, *args, **kwargs):
        pass

    def fetch_balance_sheet(self, stock_code: str) -> BalanceSheet:
        cache_key = f"hk_balance_{stock_code}"
        cached = self.cache.get(cache_key)
        if cached:
            return BalanceSheet(**cached)

        df = self._fetch_report(stock_code, "资产负债表")
        if df is None or df.empty:
            raise DataMissingError(stock_code=stock_code, missing_fields=["balance_sheet"])

        latest = self._get_latest_period(df)
        if latest is None or latest.empty:
            raise DataMissingError(stock_code=stock_code, missing_fields=["balance_sheet"])

        amount_map = self._build_amount_map(latest)

        result = BalanceSheet(
            cash_and_equivalents=self._sum_items(amount_map, _BS_ITEM_MAP["cash_and_equivalents"]),
            total_current_assets=self._sum_items(amount_map, _BS_ITEM_MAP["total_current_assets"]),
            total_assets=self._sum_items(amount_map, _BS_ITEM_MAP["total_assets"]),
            total_current_liabilities=self._sum_items(amount_map, _BS_ITEM_MAP["total_current_liabilities"]),
            total_liabilities=self._sum_items(amount_map, _BS_ITEM_MAP["total_liabilities"]),
            interest_bearing_debt=self._sum_items(amount_map, _BS_DEBT_ITEMS),
            net_assets=self._sum_items(amount_map, _BS_ITEM_MAP["net_assets"]),
        )
        self.cache.set(cache_key, self._to_dict(result))
        return result

    def fetch_income_statement(self, stock_code: str) -> tuple[IncomeStatement, bool]:
        cache_key = f"hk_income_{stock_code}"
        cached = self.cache.get(cache_key)
        if cached:
            estimated = cached.pop("_estimated", False)
            return IncomeStatement(**cached), estimated

        df = self._fetch_report(stock_code, "利润表")
        if df is None or df.empty:
            raise DataMissingError(stock_code=stock_code, missing_fields=["income_statement"])

        latest = self._get_latest_period(df)
        if latest is None or latest.empty:
            raise DataMissingError(stock_code=stock_code, missing_fields=["income_statement"])

        amount_map = self._build_amount_map(latest)
        estimated = False

        result = IncomeStatement(
            revenue=self._sum_items(amount_map, _INC_ITEM_MAP["revenue"]),
            operating_cost=self._sum_items(amount_map, _INC_ITEM_MAP["operating_cost"]),
            net_profit=self._sum_items(amount_map, _INC_ITEM_MAP["net_profit"]),
            deducted_net_profit=self._sum_items(amount_map, _INC_ITEM_MAP["deducted_net_profit"]),
        )
        d = self._to_dict(result)
        d["_estimated"] = estimated
        self.cache.set(cache_key, d)
        return result, estimated

    def fetch_cash_flow(self, stock_code: str) -> CashFlowStatement:
        cache_key = f"hk_cashflow_{stock_code}"
        cached = self.cache.get(cache_key)
        if cached:
            return CashFlowStatement(**cached)

        df = self._fetch_report(stock_code, "现金流量表")
        if df is None or df.empty:
            raise DataMissingError(stock_code=stock_code, missing_fields=["cash_flow"])

        latest = self._get_latest_period(df)
        if latest is None or latest.empty:
            raise DataMissingError(stock_code=stock_code, missing_fields=["cash_flow"])

        amount_map = self._build_amount_map(latest)

        ocf = self._sum_items(amount_map, _CF_ITEM_MAP["operating_cash_flow"])
        capex = self._sum_items(amount_map, _CF_ITEM_MAP["capital_expenditure"])

        result = CashFlowStatement(
            operating_cash_flow=ocf,
            capital_expenditure=capex,
            free_cash_flow=ocf + capex if ocf != 0 and capex != 0 else 0,
        )
        self.cache.set(cache_key, self._to_dict(result))
        return result

    def fetch_multi_year_deducted_profit(self, stock_code: str, years: int = 3) -> list[float]:
        cache_key = f"hk_multi_year_profit_{stock_code}_{years}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        df = self._fetch_report(stock_code, "利润表")
        if df is None or df.empty:
            return []

        date_col = "STD_REPORT_DATE" if "STD_REPORT_DATE" in df.columns else "REPORT_DATE"
        periods = df[date_col].unique()
        periods = sorted(periods, reverse=True)[:years]

        profit_col_candidates = ["004025002", "004012999"]
        profits = []
        for period in periods:
            period_df = df[df[date_col] == period]
            amount_map = self._build_amount_map(period_df)
            val = 0.0
            for col in profit_col_candidates:
                if col in amount_map and amount_map[col] != 0:
                    val = amount_map[col]
                    break
            profits.append(val)

        self.cache.set(cache_key, profits)
        return profits

    def _fetch_report(self, stock_code: str, report_type: str) -> pd.DataFrame | None:
        try:
            df = ak.stock_financial_hk_report_em(
                stock=stock_code, symbol=report_type, indicator="年度"
            )
            self._rate_limit_pause()
            return df
        except Exception as e:
            logger.warning(f"港股{stock_code}{report_type}获取失败: {type(e).__name__}: {e}")
            return None

    @staticmethod
    def _get_latest_period(df: pd.DataFrame) -> pd.DataFrame | None:
        date_col = None
        for col in ["STD_REPORT_DATE", "REPORT_DATE"]:
            if col in df.columns:
                date_col = col
                break
        if date_col is None:
            return None
        latest_date = df[date_col].max()
        return df[df[date_col] == latest_date]

    @staticmethod
    def _build_amount_map(period_df: pd.DataFrame) -> dict[str, float]:
        result = {}
        for _, row in period_df.iterrows():
            code = str(row.get("STD_ITEM_CODE", ""))
            amount = row.get("AMOUNT", 0)
            if amount is None or (isinstance(amount, float) and math.isnan(amount)):
                amount = 0.0
            result[code] = float(amount)
        return result

    @staticmethod
    def _sum_items(amount_map: dict, item_codes: list[str]) -> float:
        total = 0.0
        for code in item_codes:
            val = amount_map.get(code, 0.0)
            if val != 0:
                total += val
        return total

    @staticmethod
    def _to_dict(obj) -> dict:
        return {f.name: getattr(obj, f.name) for f in obj.__dataclass_fields__.values()}
