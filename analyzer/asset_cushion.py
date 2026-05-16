import logging

from config.settings import AssetCushionConfig
from common.models import StockFullData, AssetCushionResult, AssetCushionTier
from common.exceptions import DataValidationError

logger = logging.getLogger(__name__)


class AssetCushionAnalyzer:
    def __init__(self, config: AssetCushionConfig):
        self.config = config

    def calculate(self, stock: StockFullData) -> AssetCushionResult:
        market_cap = stock.market.total_market_cap
        if market_cap <= 0:
            raise DataValidationError(stock_code=stock.info.code, message="总市值为0或负值")

        conservative_cash_net = stock.balance.cash_and_equivalents - stock.balance.total_liabilities
        loose_cash_net = stock.balance.cash_and_equivalents - stock.balance.interest_bearing_debt
        conservative_ratio = conservative_cash_net / market_cap
        loose_ratio = loose_cash_net / market_cap
        current_asset_net = stock.balance.total_current_assets - stock.balance.total_liabilities
        current_asset_net_ratio = current_asset_net / market_cap

        tier = self._classify_tier(
            conservative_cash_net=conservative_cash_net,
            loose_cash_net=loose_cash_net,
            conservative_ratio=conservative_ratio,
            loose_ratio=loose_ratio,
            current_asset_net_ratio=current_asset_net_ratio,
        )

        return AssetCushionResult(
            conservative_cash_net=conservative_cash_net,
            loose_cash_net=loose_cash_net,
            conservative_ratio=conservative_ratio,
            loose_ratio=loose_ratio,
            current_asset_net_ratio=current_asset_net_ratio,
            tier=tier,
        )

    def _classify_tier(
        self,
        conservative_cash_net: float,
        loose_cash_net: float,
        conservative_ratio: float,
        loose_ratio: float,
        current_asset_net_ratio: float,
    ) -> AssetCushionTier:
        t0 = self.config.t0
        t1 = self.config.t1
        t2 = self.config.t2

        if conservative_ratio >= t0.min_conservative_ratio and loose_ratio >= t0.min_loose_ratio:
            return AssetCushionTier.T0

        t1_cond = loose_ratio >= t1.min_loose_ratio
        if t1.require_positive_conservative:
            t1_cond = t1_cond and conservative_cash_net > 0
        if t1_cond:
            return AssetCushionTier.T1

        t2_cond = True
        if t2.require_positive_loose:
            t2_cond = loose_cash_net > 0
        if t2_cond and current_asset_net_ratio > t2.min_current_asset_net_ratio:
            return AssetCushionTier.T2

        return AssetCushionTier.FAIL

    def calc_continuous_bonus(self, result: AssetCushionResult, config) -> float:
        from common.continuous_mapping import apply_mapping

        conservative_bonus = apply_mapping(result.conservative_ratio, config.conservative_ratio_mapping)
        loose_bonus = apply_mapping(result.loose_ratio, config.loose_ratio_mapping)
        return (conservative_bonus + loose_bonus) / 2.0
