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

    def calc_continuous_score(self, stock: StockFullData, result: RedemptionSafetyResult, config) -> tuple[float, float, float]:
        from common.continuous_mapping import apply_mapping

        if not result.has_redemption_logic:
            return config.base_fail_score, 0.0, config.base_fail_score

        bonuses = []

        if result.dividend_path:
            div_yield = getattr(stock.dividend, "dividend_yield", 0.0) if stock.dividend else 0.0
            div_years = float(getattr(stock.dividend, "dividend_years", 0) if stock.dividend else 0)
            div_yield_score = apply_mapping(div_yield, config.dividend_yield_mapping)
            div_years_score = apply_mapping(div_years, config.dividend_years_mapping)
            dividend_bonus = div_yield_score * config.dividend_yield_weight + div_years_score * config.dividend_years_weight
            bonuses.append(dividend_bonus)

        if result.earnings_path:
            profits = stock.multi_year_deducted_profits
            if len(profits) >= 2 and profits[1] != 0:
                intensity = (profits[0] - profits[1]) / abs(profits[1])
                intensity = max(0.0, min(1.0, intensity))
            else:
                intensity = 0.0
            earnings_score = apply_mapping(intensity, config.earnings_recovery_mapping)
            earnings_bonus = earnings_score * config.earnings_recovery_weight
            bonuses.append(earnings_bonus)

        if result.event_path:
            bonuses.append(10.0 * config.earnings_recovery_weight)

        best_bonus = max(bonuses) if bonuses else 0.0
        final_score = config.base_pass_score + best_bonus
        final_score = max(0.0, min(100.0, final_score))

        return final_score, best_bonus, config.base_pass_score
