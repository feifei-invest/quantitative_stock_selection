import logging
import math
from typing import Optional

import akshare as ak
import pandas as pd

from fetcher.base_fetcher import BaseFetcher
from fetcher.data_cache import DataCache
from config.settings import Settings
from common.models import BalanceSheet, IncomeStatement, CashFlowStatement
from common.exceptions import DataFetchError, DataMissingError

logger = logging.getLogger(__name__)


class FinanceFetcher(BaseFetcher):
    def __init__(self, settings: Settings, cache: DataCache):
        super().__init__(settings)
        self.cache = cache

    def fetch(self, *args, **kwargs):
        pass

    def fetch_balance_sheet(self, stock_code: str) -> BalanceSheet:
        cache_key = f"balance_{stock_code}"
        cached = self.cache.get(cache_key)
        if cached:
            return BalanceSheet(**cached)

        try:
            df = ak.stock_financial_report_sina(stock=stock_code, symbol="资产负债表")
            self._rate_limit_pause()
        except Exception as e:
            raise DataFetchError(stock_code=stock_code, data_type="balance_sheet", message=str(e))

        if df is None or df.empty:
            raise DataMissingError(stock_code=stock_code, missing_fields=["balance_sheet"])

        row = df.iloc[0]
        cash = self._safe_float(row, "货币资金")
        current_assets = self._safe_float(row, "流动资产合计")
        total_assets = self._safe_float(row, "资产总计")
        current_liab = self._safe_float(row, "流动负债合计")
        total_liab = self._safe_float(row, "负债合计")
        short_loan = self._safe_float(row, "短期借款")
        long_loan = self._safe_float(row, "长期借款")
        bonds = self._safe_float(row, "应付债券")
        net_assets = self._safe_float(row, "所有者权益(或股东权益)合计")
        if net_assets == 0:
            net_assets = self._safe_float(row, "归属于母公司股东权益合计")

        result = BalanceSheet(
            cash_and_equivalents=cash,
            total_current_assets=current_assets,
            total_assets=total_assets,
            total_current_liabilities=current_liab,
            total_liabilities=total_liab,
            interest_bearing_debt=short_loan + long_loan + bonds,
            net_assets=net_assets,
        )
        self.cache.set(cache_key, self._to_dict(result))
        return result

    def fetch_income_statement(self, stock_code: str) -> IncomeStatement:
        cache_key = f"income_{stock_code}"
        cached = self.cache.get(cache_key)
        if cached:
            return IncomeStatement(**cached)

        try:
            df = ak.stock_financial_report_sina(stock=stock_code, symbol="利润表")
            self._rate_limit_pause()
        except Exception as e:
            raise DataFetchError(stock_code=stock_code, data_type="income_statement", message=str(e))

        if df is None or df.empty:
            raise DataMissingError(stock_code=stock_code, missing_fields=["income_statement"])

        row = df.iloc[0]
        result = IncomeStatement(
            revenue=self._safe_float(row, "营业收入"),
            operating_cost=self._safe_float(row, "营业成本"),
            net_profit=self._safe_float(row, "净利润"),
            deducted_net_profit=self._safe_float(row, "扣除非经常性损益后的净利润"),
        )
        self.cache.set(cache_key, self._to_dict(result))
        return result

    def fetch_cash_flow(self, stock_code: str) -> CashFlowStatement:
        cache_key = f"cashflow_{stock_code}"
        cached = self.cache.get(cache_key)
        if cached:
            return CashFlowStatement(**cached)

        try:
            df = ak.stock_financial_report_sina(stock=stock_code, symbol="现金流量表")
            self._rate_limit_pause()
        except Exception as e:
            raise DataFetchError(stock_code=stock_code, data_type="cash_flow", message=str(e))

        if df is None or df.empty:
            raise DataMissingError(stock_code=stock_code, missing_fields=["cash_flow"])

        row = df.iloc[0]
        ocf = self._safe_float(row, "经营活动产生的现金流量净额")
        capex = self._safe_float(row, "购建固定资产、无形资产和其他长期资产支付的现金")
        fcf = ocf - capex

        result = CashFlowStatement(
            operating_cash_flow=ocf,
            capital_expenditure=capex,
            free_cash_flow=fcf,
        )
        self.cache.set(cache_key, self._to_dict(result))
        return result

    def fetch_multi_year_deducted_profit(self, stock_code: str, years: int = 3) -> list[float]:
        cache_key = f"multi_year_profit_{stock_code}_{years}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            df = ak.stock_financial_report_sina(stock=stock_code, symbol="利润表")
            self._rate_limit_pause()
        except Exception as e:
            raise DataFetchError(stock_code=stock_code, data_type="multi_year_profit", message=str(e))

        if df is None or df.empty:
            return []

        col = "扣除非经常性损益后的净利润"
        if col not in df.columns:
            return []

        recent = df.head(years)
        profits = []
        for _, row in recent.iterrows():
            val = self._safe_float(row, col)
            profits.append(val)

        self.cache.set(cache_key, profits)
        return profits

    @staticmethod
    def _safe_float(row: pd.Series, col: str) -> float:
        try:
            val = row.get(col, 0)
            if val is None or (isinstance(val, float) and math.isnan(val)):
                return 0.0
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _to_dict(obj) -> dict:
        return {f.name: getattr(obj, f.name) for f in obj.__dataclass_fields__.values()}
