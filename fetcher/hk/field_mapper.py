import logging
import math

import yaml
import pandas as pd

logger = logging.getLogger(__name__)


class FieldMapper:
    def __init__(self, mapping_path: str = "config/hk_field_mapping.yaml"):
        with open(mapping_path, "r", encoding="utf-8") as f:
            self._mapping = yaml.safe_load(f)
        self._balance_map = self._mapping.get("balance_sheet", {})
        self._income_map = self._mapping.get("income_statement", {})
        self._cashflow_map = self._mapping.get("cash_flow", {})
        self._debt_items = self._mapping.get("interest_bearing_debt_items", [])

    def map_balance_sheet(self, row: pd.Series) -> dict:
        result = {}
        for std_field, candidates in self._balance_map.items():
            result[std_field] = self._match_field(row, candidates)
        result["interest_bearing_debt"] = self._calc_interest_bearing_debt(row)
        return result

    def map_income_statement(self, row: pd.Series) -> tuple[dict, bool]:
        result = {}
        estimated = False
        for std_field, candidates in self._income_map.items():
            result[std_field] = self._match_field(row, candidates)

        if std_field == "deducted_net_profit" and abs(result.get("deducted_net_profit", 0)) < 1e-6:
            np_val = result.get("net_profit", 0)
            if abs(np_val) > 1e-6:
                result["deducted_net_profit"] = np_val
                estimated = True
                logger.debug("扣非净利润缺失, 使用净利润替代(估算)")

        return result, estimated

    def map_cash_flow(self, row: pd.Series) -> dict:
        result = {}
        for std_field, candidates in self._cashflow_map.items():
            result[std_field] = self._match_field(row, candidates)
        ocf = result.get("operating_cash_flow", 0)
        capex = result.get("capital_expenditure", 0)
        result["free_cash_flow"] = ocf - capex
        return result

    def _calc_interest_bearing_debt(self, row: pd.Series) -> float:
        total = 0.0
        for item_name in self._debt_items:
            total += self._safe_float(row, item_name)
        return total

    def _match_field(self, row: pd.Series, candidates: list) -> float:
        for name in candidates:
            val = self._safe_float(row, name)
            if not math.isnan(val) and val != 0:
                return val
        return 0.0

    @staticmethod
    def _safe_float(row: pd.Series, col: str) -> float:
        try:
            val = row.get(col, 0)
            if val is None or (isinstance(val, float) and math.isnan(val)):
                return 0.0
            return float(val)
        except (ValueError, TypeError):
            return 0.0
