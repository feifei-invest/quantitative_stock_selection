import logging

from config.settings import OperationSafetyConfig
from common.models import StockFullData, OperationSafetyResult, OperationStatus

logger = logging.getLogger(__name__)


class OperationSafetyAnalyzer:
    def __init__(self, config: OperationSafetyConfig):
        self.config = config

    def evaluate(self, stock: StockFullData) -> OperationSafetyResult:
        fcf = stock.cash_flow.free_cash_flow
        ocf = stock.cash_flow.operating_cash_flow
        capex = stock.cash_flow.capital_expenditure

        if abs(ocf) < 1e-6:
            capex_ratio = float("inf")
        else:
            capex_ratio = abs(capex) / abs(ocf) if ocf > 0 else float("inf")

        is_fcf_positive = fcf > 0
        is_capex_low = capex_ratio < self.config.max_capex_ratio

        if is_fcf_positive and is_capex_low:
            status = OperationStatus.PASS
        elif is_fcf_positive:
            status = OperationStatus.PARTIAL
        else:
            status = OperationStatus.FAIL

        return OperationSafetyResult(
            free_cash_flow=fcf,
            capex_ratio=capex_ratio,
            is_fcf_positive=is_fcf_positive,
            is_capex_ratio_low=is_capex_low,
            status=status,
        )

    def calc_continuous_adjustment(self, result: OperationSafetyResult, config) -> float:
        from common.continuous_mapping import apply_mapping

        if result.status == OperationStatus.FAIL:
            return 0.0

        max_capex = self.config.max_capex_ratio
        if result.status == OperationStatus.PASS:
            reversed_val = max_capex - result.capex_ratio
            return apply_mapping(reversed_val, config.capex_ratio_mapping)

        if result.status == OperationStatus.PARTIAL:
            penalty = apply_mapping(result.capex_ratio, config.capex_ratio_mapping)
            return -penalty

        return 0.0
