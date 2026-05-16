import logging

from config.settings import DelistingConfig
from common.models import StockFullData

logger = logging.getLogger(__name__)


class DelistingFilter:
    def __init__(self, config: DelistingConfig):
        self.config = config

    def is_delisting_risk(self, stock: StockFullData) -> bool:
        if self._check_st_status(stock.info.name):
            logger.info(f"剔除{stock.info.code} {stock.info.name}: ST标记")
            return True
        if self._check_financial_risk(stock):
            logger.info(f"剔除{stock.info.code} {stock.info.name}: 财务退市风险")
            return True
        if self._check_negative_assets(stock):
            logger.info(f"剔除{stock.info.code} {stock.info.name}: 净资产为负")
            return True
        return False

    def filter(self, stocks: list[StockFullData]) -> list[StockFullData]:
        before = len(stocks)
        result = [s for s in stocks if not self.is_delisting_risk(s)]
        after = len(result)
        logger.info(f"退市风险过滤: {before}只 -> {after}只, 剔除{before - after}只")
        return result

    def _check_st_status(self, stock_name: str) -> bool:
        for kw in self.config.st_keywords:
            if kw in stock_name:
                return True
        return False

    def _check_financial_risk(self, stock: StockFullData) -> bool:
        return (
            stock.income.deducted_net_profit < 0
            and stock.income.revenue < self.config.min_revenue
        )

    def _check_negative_assets(self, stock: StockFullData) -> bool:
        if self.config.require_positive_net_assets:
            return stock.balance.net_assets < 0
        return False
