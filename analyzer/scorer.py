import logging

from config.settings import ScoringConfig
from common.models import (
    StockFullData,
    AssetCushionResult,
    AssetCushionTier,
    OperationSafetyResult,
    OperationStatus,
    RedemptionSafetyResult,
    ScoredResult,
)
from common.continuous_mapping import apply_mapping

logger = logging.getLogger(__name__)


class Scorer:
    def __init__(self, config: ScoringConfig):
        self.config = config

    def score(
        self,
        stock: StockFullData,
        asset_result: AssetCushionResult,
        operation_result: OperationSafetyResult,
        redemption_result: RedemptionSafetyResult,
        asset_analyzer=None,
        operation_analyzer=None,
        redemption_analyzer=None,
        deducted_net_profit_is_estimated: bool = False,
    ) -> ScoredResult:
        is_continuous = (
            self.config.asset_continuous.enabled
            or self.config.operation_continuous.enabled
            or self.config.redemption_continuous.enabled
        )

        asset_score, asset_bonus = self._calc_asset_score(asset_result, asset_analyzer)
        operation_score, operation_adj = self._calc_operation_score(operation_result, operation_analyzer)
        redemption_score, redemption_bonus, redemption_base = self._calc_redemption_score(
            stock, redemption_result, redemption_analyzer
        )

        total = (
            asset_score * self.config.asset_cushion_weight
            + operation_score * self.config.operation_safety_weight
            + redemption_score * self.config.redemption_safety_weight
        )

        tie_break_score = 0.0
        if self.config.tie_break.enabled:
            tie_break_score = self._calc_tie_break_score(stock, asset_result, operation_result)

        return ScoredResult(
            stock_code=stock.info.code,
            stock_name=stock.info.name,
            asset_cushion_tier=asset_result.tier.value,
            conservative_ratio=asset_result.conservative_ratio,
            loose_ratio=asset_result.loose_ratio,
            free_cash_flow=operation_result.free_cash_flow,
            capex_ratio=operation_result.capex_ratio,
            redemption_path_type=redemption_result.path_type.value,
            asset_cushion_score=asset_score,
            operation_safety_score=operation_score,
            redemption_safety_score=redemption_score,
            total_score=total,
            market=stock.info.market,
            currency="HKD" if stock.info.market == "HK" else "CNY",
            deducted_net_profit_is_estimated=deducted_net_profit_is_estimated,
            asset_continuous_bonus=asset_bonus,
            operation_continuous_adjustment=operation_adj,
            redemption_continuous_bonus=redemption_bonus,
            redemption_base_score=redemption_base,
            tie_break_score=tie_break_score,
            scoring_mode="continuous" if is_continuous else "discrete",
        )

    @staticmethod
    def rank_results(results: list[ScoredResult]) -> list[ScoredResult]:
        results.sort(key=lambda x: (x.total_score, x.tie_break_score), reverse=True)
        for i, r in enumerate(results, 1):
            r.rank = i
        return results

    def _calc_asset_score(self, asset_result: AssetCushionResult, asset_analyzer=None) -> tuple[float, float]:
        base_mapping = {
            AssetCushionTier.T0: self.config.t0_score,
            AssetCushionTier.T1: self.config.t1_score,
            AssetCushionTier.T2: self.config.t2_score,
            AssetCushionTier.FAIL: self.config.fail_score,
        }
        base_score = base_mapping.get(asset_result.tier, 0.0)
        bonus = 0.0

        if self.config.asset_continuous.enabled and asset_analyzer is not None and asset_result.tier != AssetCushionTier.FAIL:
            bonus = asset_analyzer.calc_continuous_bonus(asset_result, self.config.asset_continuous)
            base_score = max(0.0, min(100.0, base_score + bonus))

        return base_score, bonus

    def _calc_operation_score(self, operation_result: OperationSafetyResult, operation_analyzer=None) -> tuple[float, float]:
        base_mapping = {
            OperationStatus.PASS: self.config.operation_pass_score,
            OperationStatus.PARTIAL: self.config.operation_partial_score,
            OperationStatus.FAIL: self.config.operation_fail_score,
        }
        base_score = base_mapping.get(operation_result.status, 0.0)
        adjustment = 0.0

        if self.config.operation_continuous.enabled and operation_analyzer is not None and operation_result.status != OperationStatus.FAIL:
            adjustment = operation_analyzer.calc_continuous_adjustment(operation_result, self.config.operation_continuous)
            base_score = max(0.0, min(100.0, base_score + adjustment))

        return base_score, adjustment

    def _calc_redemption_score(
        self, stock: StockFullData, redemption_result: RedemptionSafetyResult, redemption_analyzer=None
    ) -> tuple[float, float, float]:
        if not self.config.redemption_continuous.enabled or redemption_analyzer is None:
            base_score = self.config.redemption_pass_score if redemption_result.has_redemption_logic else self.config.redemption_fail_score
            return base_score, 0.0, base_score

        score, bonus, base = redemption_analyzer.calc_continuous_score(stock, redemption_result, self.config.redemption_continuous)
        return score, bonus, base

    def _calc_tie_break_score(
        self, stock: StockFullData, asset_result: AssetCushionResult, operation_result: OperationSafetyResult
    ) -> float:
        cfg = self.config.tie_break
        if not cfg.enabled:
            return 0.0

        factor_values = {}
        factor_values["conservative_ratio"] = asset_result.conservative_ratio
        factor_values["loose_ratio"] = asset_result.loose_ratio
        factor_values["dividend_yield"] = getattr(stock.dividend, "dividend_yield", 0.0) if stock.dividend else 0.0
        factor_values["fcf_to_market_cap"] = 0.0
        if stock.market and stock.market.total_market_cap > 0 and operation_result.free_cash_flow > 0:
            factor_values["fcf_to_market_cap"] = operation_result.free_cash_flow / stock.market.total_market_cap

        total = 0.0
        for i, factor in enumerate(cfg.factors):
            weight = cfg.factor_weights[i] if i < len(cfg.factor_weights) else 0.0
            val = factor_values.get(factor, 0.0)
            normalized = (val + 5.0) / 10.0
            normalized = max(0.0, min(1.0, normalized))
            total += weight * normalized

        return total
