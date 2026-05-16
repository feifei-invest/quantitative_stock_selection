import sys
import time
import logging

from common.logger import LoggerManager
from common.models import StockFullData, ScoredResult
from config.settings import Settings, AssetCushionConfig, ScoringConfig
from fetcher.data_cache import DataCache
from fetcher.index_fetcher import IndexFetcher
from fetcher.finance_fetcher import FinanceFetcher
from fetcher.market_fetcher import MarketFetcher
from fetcher.dividend_fetcher import DividendFetcher
from fetcher.hk.hk_index_fetcher import HKIndexFetcher
from fetcher.hk.hk_finance_fetcher import HKFinanceFetcher
from fetcher.hk.hk_market_fetcher import HKMarketFetcher
from fetcher.hk.hk_dividend_fetcher import HKDividendFetcher
from analyzer.delisting_filter import DelistingFilter
from analyzer.hk_delisting_filter import HKDelistingFilter
from analyzer.asset_cushion import AssetCushionAnalyzer
from analyzer.operation_safety import OperationSafetyAnalyzer
from analyzer.redemption_safety import RedemptionSafetyAnalyzer
from analyzer.scorer import Scorer
from output.csv_writer import CsvWriter
from output.table_printer import TablePrinter
from common.exceptions import (
    DataFetchError,
    DataMissingError,
    DataValidationError,
    StockSelectionError,
)


def run_a_stock_selection(settings: Settings, cache: DataCache, logger: logging.Logger) -> list[ScoredResult]:
    logger.info("-" * 40 + " A股选股 " + "-" * 40)

    index_fetcher = IndexFetcher(settings, cache)
    finance_fetcher = FinanceFetcher(settings, cache)
    market_fetcher = MarketFetcher(settings, cache)
    dividend_fetcher = DividendFetcher(settings, cache)

    delisting_filter = DelistingFilter(settings.delisting)
    ac_config = settings.asset_cushion
    sc_config = settings.scoring
    asset_analyzer = AssetCushionAnalyzer(ac_config)
    operation_analyzer = OperationSafetyAnalyzer(settings.operation_safety)
    redemption_analyzer = RedemptionSafetyAnalyzer(settings.redemption_safety)
    scorer = Scorer(sc_config)

    logger.info("[Step 1] 获取沪深300成分股...")
    try:
        constituents = index_fetcher.fetch()
    except DataFetchError as e:
        logger.error(f"获取沪深300成分股失败: {e}")
        return []
    logger.info(f"沪深300成分股: {len(constituents)}只")

    logger.info("[Step 2] 批量获取市值数据...")
    codes = [s.code for s in constituents]
    try:
        market_data_map = market_fetcher.fetch_batch_market_data(codes)
    except DataFetchError as e:
        logger.error(f"获取市值数据失败: {e}")
        return []
    logger.info(f"市值数据获取完成: {len(market_data_map)}只")

    logger.info("[Step 3] 获取财务数据并组装...")
    full_data_list = []
    for i, info in enumerate(constituents):
        if info.code not in market_data_map:
            continue
        try:
            balance = finance_fetcher.fetch_balance_sheet(info.code)
            income = finance_fetcher.fetch_income_statement(info.code)
            cash_flow = finance_fetcher.fetch_cash_flow(info.code)
            multi_profits = finance_fetcher.fetch_multi_year_deducted_profit(info.code)
            dividend = dividend_fetcher.fetch_dividend_data(info.code, market_data_map[info.code].latest_price)
            stock_data = StockFullData(
                info=info, balance=balance, income=income, cash_flow=cash_flow,
                market=market_data_map[info.code], dividend=dividend,
                multi_year_deducted_profits=multi_profits,
            )
            full_data_list.append(stock_data)
        except (DataMissingError, DataValidationError) as e:
            logger.warning(f"股票{info.code}数据不完整: {e}")
            full_data_list.append(StockFullData(info=info, market=market_data_map[info.code], is_data_complete=False, missing_fields=[str(e)]))
        except Exception as e:
            logger.error(f"股票{info.code}数据处理异常: {e}")
        if (i + 1) % 50 == 0:
            logger.info(f"  进度: {i + 1}/{len(constituents)}")

    logger.info(f"财务数据组装完成: {len(full_data_list)}只")
    return _evaluate_and_score(full_data_list, delisting_filter, asset_analyzer, operation_analyzer, redemption_analyzer, scorer, logger)


def run_hk_stock_selection(settings: Settings, cache: DataCache, logger: logging.Logger) -> list[ScoredResult]:
    logger.info("-" * 40 + " 港股通选股 " + "-" * 40)

    hk_cfg = settings.hk_stock

    index_fetcher = HKIndexFetcher(settings, cache)
    finance_fetcher = HKFinanceFetcher(settings, cache)
    market_fetcher = HKMarketFetcher(settings, cache)
    dividend_fetcher = HKDividendFetcher(settings, cache)

    delisting_filter = HKDelistingFilter(hk_cfg.delisting)
    ac_config = hk_cfg.asset_cushion if hk_cfg.asset_cushion else settings.asset_cushion
    sc_config = hk_cfg.scoring if hk_cfg.scoring else settings.scoring
    asset_analyzer = AssetCushionAnalyzer(ac_config)
    operation_analyzer = OperationSafetyAnalyzer(settings.operation_safety)
    redemption_analyzer = RedemptionSafetyAnalyzer(settings.redemption_safety)
    scorer = Scorer(sc_config)

    logger.info("[Step 1] 获取港股通成分股...")
    try:
        constituents = index_fetcher.fetch()
    except DataFetchError as e:
        logger.error(f"获取港股通成分股失败: {e}")
        return []
    logger.info(f"港股通成分股: {len(constituents)}只")

    logger.info("[Step 2] 批量获取市值数据...")
    codes = [s.code for s in constituents]
    try:
        market_data_map = market_fetcher.fetch_batch_market_data(codes)
    except DataFetchError as e:
        logger.error(f"获取港股市值数据失败: {e}")
        return []
    logger.info(f"港股市值数据获取完成: {len(market_data_map)}只")

    logger.info("[Step 3] 获取财务数据并组装...")
    full_data_list = []
    for i, info in enumerate(constituents):
        if info.code not in market_data_map:
            continue
        try:
            balance = finance_fetcher.fetch_balance_sheet(info.code)
            income, estimated = finance_fetcher.fetch_income_statement(info.code)
            cash_flow = finance_fetcher.fetch_cash_flow(info.code)
            multi_profits = finance_fetcher.fetch_multi_year_deducted_profit(info.code)
            dividend = dividend_fetcher.fetch_dividend_data(info.code, market_data_map[info.code].latest_price)
            stock_data = StockFullData(
                info=info, balance=balance, income=income, cash_flow=cash_flow,
                market=market_data_map[info.code], dividend=dividend,
                multi_year_deducted_profits=multi_profits,
            )
            stock_data._dkpe_estimated = estimated
            full_data_list.append(stock_data)
        except (DataMissingError, DataValidationError) as e:
            logger.warning(f"港股{info.code}数据不完整: {e}")
            full_data_list.append(StockFullData(info=info, market=market_data_map[info.code], is_data_complete=False, missing_fields=[str(e)]))
        except Exception as e:
            logger.error(f"港股{info.code}数据处理异常: {e}")
        if (i + 1) % 50 == 0:
            logger.info(f"  进度: {i + 1}/{len(constituents)}")

    logger.info(f"港股财务数据组装完成: {len(full_data_list)}只")
    return _evaluate_and_score(full_data_list, delisting_filter, asset_analyzer, operation_analyzer, redemption_analyzer, scorer, logger)


def _evaluate_and_score(full_data_list, delisting_filter, asset_analyzer, operation_analyzer, redemption_analyzer, scorer, logger):
    logger.info("[Step 4] 退市风险过滤...")
    filtered = delisting_filter.filter(full_data_list)

    complete_data = [s for s in filtered if s.is_data_complete]
    logger.info(f"数据完整股票: {len(complete_data)}只")

    logger.info("[Step 5] 综合评估与评分...")
    scored_results = []
    for stock in complete_data:
        try:
            asset_result = asset_analyzer.calculate(stock)
            operation_result = operation_analyzer.evaluate(stock)
            redemption_result = redemption_analyzer.evaluate(stock)
            estimated = getattr(stock, '_dkpe_estimated', False)
            scored = scorer.score(
                stock, asset_result, operation_result, redemption_result,
                asset_analyzer=asset_analyzer, operation_analyzer=operation_analyzer,
                redemption_analyzer=redemption_analyzer,
                deducted_net_profit_is_estimated=estimated,
            )
            scored_results.append(scored)
        except DataValidationError as e:
            logger.warning(f"股票{stock.info.code}评分跳过: {e}")
        except Exception as e:
            logger.error(f"股票{stock.info.code}评分异常: {e}")

    scored_results = Scorer.rank_results(scored_results)
    return scored_results


def main():
    start_time = time.time()

    settings = Settings.load("config.yaml")
    logger = LoggerManager.setup(
        log_dir=settings.output.log_dir,
        log_level=settings.output.log_level,
    )
    logger.info("=" * 60)
    logger.info("价值股票量化选股系统启动")
    logger.info(f"市场模式: {settings.market}")
    logger.info("=" * 60)

    cache = DataCache(
        cache_dir=settings.data_source.cache_dir,
        expire_hours=settings.data_source.finance_expire_hours,
    )

    csv_writer = CsvWriter(csv_dir=settings.output.csv_dir, encoding=settings.output.csv_encoding)
    table_printer = TablePrinter(max_rows=settings.output.terminal_max_rows)

    all_results = []

    if settings.market in ("A", "ALL"):
        a_results = run_a_stock_selection(settings, cache, logger)
        all_results.extend(a_results)
        logger.info(f"A股选股完成: {len(a_results)}只入选")

    if settings.market in ("HK", "ALL"):
        hk_results = run_hk_stock_selection(settings, cache, logger)
        all_results.extend(hk_results)
        logger.info(f"港股选股完成: {len(hk_results)}只入选")

    all_results = Scorer.rank_results(all_results)

    logger.info("[输出] 输出结果...")
    csv_path = csv_writer.write(all_results)
    table_printer.print(all_results)

    elapsed = time.time() - start_time
    logger.info(f"全部选股完成! 共{len(all_results)}只股票入选, 耗时{elapsed:.1f}秒")
    if csv_path:
        logger.info(f"结果文件: {csv_path}")

    return all_results


if __name__ == "__main__":
    main()
