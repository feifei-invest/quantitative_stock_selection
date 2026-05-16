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
    ) -> ScoredResult:
        asset_score = self._calc_asset_score(asset_result.tier)
        operation_score = self._calc_operation_score(operation_result.status)
        redemption_score = self._calc_redemption_score(redemption_result.has_redemption_logic)

        total = (
            asset_score * self.config.asset_cushion_weight
            + operation_score * self.config.operation_safety_weight
            + redemption_score * self.config.redemption_safety_weight
        )

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
        )

    @staticmethod
    def rank_results(results: list[ScoredResult]) -> list[ScoredResult]:
        results.sort(key=lambda x: x.total_score, reverse=True)
        for i, r in enumerate(results, 1):
            r.rank = i
        return results

    def _calc_asset_score(self, tier: AssetCushionTier) -> float:
        mapping = {
            AssetCushionTier.T0: self.config.t0_score,
            AssetCushionTier.T1: self.config.t1_score,
            AssetCushionTier.T2: self.config.t2_score,
            AssetCushionTier.FAIL: self.config.fail_score,
        }
        return mapping.get(tier, 0.0)

    def _calc_operation_score(self, status: OperationStatus) -> float:
        mapping = {
            OperationStatus.PASS: self.config.operation_pass_score,
            OperationStatus.PARTIAL: self.config.operation_partial_score,
            OperationStatus.FAIL: self.config.operation_fail_score,
        }
        return mapping.get(status, 0.0)

    def _calc_redemption_score(self, has_logic: bool) -> float:
        return self.config.redemption_pass_score if has_logic else self.config.redemption_fail_score
