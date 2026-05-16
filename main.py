import sys
import time
import logging

from common.logger import LoggerManager
from common.models import StockFullData, ScoredResult
from config.settings import Settings
from fetcher.data_cache import DataCache
from fetcher.index_fetcher import IndexFetcher
from fetcher.finance_fetcher import FinanceFetcher
from fetcher.market_fetcher import MarketFetcher
from fetcher.dividend_fetcher import DividendFetcher
from analyzer.delisting_filter import DelistingFilter
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


def main():
    start_time = time.time()

    settings = Settings.load("config.yaml")
    logger = LoggerManager.setup(
        log_dir=settings.output.log_dir,
        log_level=settings.output.log_level,
    )
    logger.info("=" * 60)
    logger.info("沪深300价值股票量化选股系统启动")
    logger.info("=" * 60)

    cache = DataCache(
        cache_dir=settings.data_source.cache_dir,
        expire_hours=settings.data_source.finance_expire_hours,
    )

    index_fetcher = IndexFetcher(settings, cache)
    finance_fetcher = FinanceFetcher(settings, cache)
    market_fetcher = MarketFetcher(settings, cache)
    dividend_fetcher = DividendFetcher(settings, cache)

    delisting_filter = DelistingFilter(settings.delisting)
    asset_analyzer = AssetCushionAnalyzer(settings.asset_cushion)
    operation_analyzer = OperationSafetyAnalyzer(settings.operation_safety)
    redemption_analyzer = RedemptionSafetyAnalyzer(settings.redemption_safety)
    scorer = Scorer(settings.scoring)

    csv_writer = CsvWriter(
        csv_dir=settings.output.csv_dir,
        encoding=settings.output.csv_encoding,
    )
    table_printer = TablePrinter(max_rows=settings.output.terminal_max_rows)

    # Step 1: 获取沪深300成分股
    logger.info("[Step 1] 获取沪深300成分股...")
    try:
        constituents = index_fetcher.fetch()
    except DataFetchError as e:
        logger.error(f"获取沪深300成分股失败: {e}")
        sys.exit(1)
    logger.info(f"沪深300成分股: {len(constituents)}只")

    # Step 2: 批量获取市值数据
    logger.info("[Step 2] 批量获取市值数据...")
    codes = [s.code for s in constituents]
    try:
        market_data_map = market_fetcher.fetch_batch_market_data(codes)
    except DataFetchError as e:
        logger.error(f"获取市值数据失败: {e}")
        sys.exit(1)
    logger.info(f"市值数据获取完成: {len(market_data_map)}只")

    # Step 3: 逐只获取财务数据并组装
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
            dividend = dividend_fetcher.fetch_dividend_data(
                info.code, market_data_map[info.code].latest_price
            )

            stock_data = StockFullData(
                info=info,
                balance=balance,
                income=income,
                cash_flow=cash_flow,
                market=market_data_map[info.code],
                dividend=dividend,
                multi_year_deducted_profits=multi_profits,
            )
            full_data_list.append(stock_data)

        except (DataMissingError, DataValidationError) as e:
            logger.warning(f"股票{info.code}数据不完整: {e}")
            stock_data = StockFullData(
                info=info,
                market=market_data_map[info.code],
                is_data_complete=False,
                missing_fields=[str(e)],
            )
            full_data_list.append(stock_data)
        except Exception as e:
            logger.error(f"股票{info.code}数据处理异常: {e}")

        if (i + 1) % 50 == 0:
            logger.info(f"  进度: {i + 1}/{len(constituents)}")

    logger.info(f"财务数据组装完成: {len(full_data_list)}只")

    # Step 4: 退市风险过滤
    logger.info("[Step 4] 退市风险过滤...")
    filtered = delisting_filter.filter(full_data_list)

    # Step 5: 仅保留数据完整的股票
    complete_data = [s for s in filtered if s.is_data_complete]
    logger.info(f"数据完整股票: {len(complete_data)}只")

    # Step 6: 综合评估与评分
    logger.info("[Step 5] 综合评估与评分...")
    scored_results = []
    for stock in complete_data:
        try:
            asset_result = asset_analyzer.calculate(stock)
            operation_result = operation_analyzer.evaluate(stock)
            redemption_result = redemption_analyzer.evaluate(stock)
            scored = scorer.score(stock, asset_result, operation_result, redemption_result)
            scored_results.append(scored)
        except DataValidationError as e:
            logger.warning(f"股票{stock.info.code}评分跳过: {e}")
        except Exception as e:
            logger.error(f"股票{stock.info.code}评分异常: {e}")

    # Step 7: 排序
    scored_results = Scorer.rank_results(scored_results)

    # Step 8: 输出
    logger.info("[Step 6] 输出结果...")
    csv_path = csv_writer.write(scored_results)
    table_printer.print(scored_results)

    elapsed = time.time() - start_time
    logger.info(f"选股完成! 共{len(scored_results)}只股票入选, 耗时{elapsed:.1f}秒")
    if csv_path:
        logger.info(f"结果文件: {csv_path}")

    return scored_results


if __name__ == "__main__":
    main()
