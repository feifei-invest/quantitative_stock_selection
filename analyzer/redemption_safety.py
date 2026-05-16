import logging

from config.settings import RedemptionSafetyConfig
from common.models import StockFullData, RedemptionSafetyResult, RedemptionPath

logger = logging.getLogger(__name__)


class RedemptionSafetyAnalyzer:
    def __init__(self, config: RedemptionSafetyConfig):
        self.config = config

    def evaluate(self, stock: StockFullData) -> RedemptionSafetyResult:
        dividend_path = self._check_dividend_path(stock)
        earnings_path = self._check_earnings_recovery(stock)
        event_path = self._check_event_path(stock)

        has_logic = dividend_path or event_path or earnings_path

        if dividend_path:
            path_type = RedemptionPath.DIVIDEND
        elif event_path:
            path_type = RedemptionPath.EVENT
        elif earnings_path:
            path_type = RedemptionPath.EARNINGS_RECOVERY
        else:
            path_type = RedemptionPath.NONE

        return RedemptionSafetyResult(
            dividend_path=dividend_path,
            event_path=event_path,
            earnings_path=earnings_path,
            has_redemption_logic=has_logic,
            path_type=path_type,
        )

    def _check_dividend_path(self, stock: StockFullData) -> bool:
        cfg = self.config.dividend
        return (
            stock.dividend.dividend_years >= cfg.min_years
            and stock.dividend.dividend_yield > cfg.min_dividend_yield
        )

    def _check_earnings_recovery(self, stock: StockFullData) -> bool:
        profits = stock.multi_year_deducted_profits
        if len(profits) < 2:
            return False

        for p in profits:
            if p <= 0:
                return False

        if len(profits) >= 2 and profits[0] > profits[1]:
            return True

        return False

    def _check_event_path(self, stock: StockFullData) -> bool:
        return False
