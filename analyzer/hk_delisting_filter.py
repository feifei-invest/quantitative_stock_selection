import logging

from config.settings import HKDelistingConfig
from common.models import StockFullData

logger = logging.getLogger(__name__)


class HKDelistingFilter:
    def __init__(self, config: HKDelistingConfig):
        self.config = config

    def is_delisting_risk(self, stock: StockFullData) -> bool:
        if self._check_low_market_cap(stock):
            logger.info(f"剔除{stock.info.code} {stock.info.name}: 市值低于最低要求")
            return True
        if self._check_negative_net_assets(stock):
            logger.info(f"剔除{stock.info.code} {stock.info.name}: 净资产为负")
            return True
        return False

    def filter(self, stocks: list[StockFullData]) -> list[StockFullData]:
        before = len(stocks)
        result = [s for s in stocks if not self.is_delisting_risk(s)]
        after = len(result)
        logger.info(f"港股退市风险过滤: {before}只 -> {after}只, 剔除{before - after}只")
        return result

    def _check_low_market_cap(self, stock: StockFullData) -> bool:
        return stock.market.total_market_cap < self.config.min_market_cap_hkd

    def _check_negative_net_assets(self, stock: StockFullData) -> bool:
        return stock.balance.net_assets < 0
