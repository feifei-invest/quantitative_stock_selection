import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.models import (
    StockFullData, StockInfo, BalanceSheet, IncomeStatement,
    CashFlowStatement, MarketData, DividendData,
    AssetCushionResult, AssetCushionTier,
    OperationSafetyResult, OperationStatus,
    RedemptionSafetyResult,
)
from config.settings import ScoringConfig, AssetCushionContinuousConfig, OperationSafetyContinuousConfig, RedemptionSafetyContinuousConfig, TieBreakConfig
from analyzer.asset_cushion import AssetCushionAnalyzer
from analyzer.operation_safety import OperationSafetyAnalyzer
from analyzer.redemption_safety import RedemptionSafetyAnalyzer
from analyzer.scorer import Scorer
from config.settings import AssetCushionConfig, OperationSafetyConfig, RedemptionSafetyConfig


def _make_stock(code="00001", name="test", market="A",
                cash=100, tca=200, ta=500, tcl=100, tl=200, debt=50, na=300,
                revenue=100, nprofit=30, dnp=25,
                ocf=40, capex=-10,
                div_yield=0.03, div_years=5, mcap=1000):
    info = StockInfo(code=code, name=name, market=market)
    balance = BalanceSheet(cash_and_equivalents=cash, total_current_assets=tca, total_assets=ta,
                           total_current_liabilities=tcl, total_liabilities=tl, interest_bearing_debt=debt, net_assets=na)
    income = IncomeStatement(revenue=revenue, net_profit=nprofit, deducted_net_profit=dnp)
    cash_flow = CashFlowStatement(operating_cash_flow=ocf, capital_expenditure=capex, free_cash_flow=ocf + capex)
    market_data = MarketData(total_market_cap=mcap, latest_price=10.0)
    dividend = DividendData(dividend_years=div_years, dividend_yield=div_yield)
    return StockFullData(info=info, balance=balance, income=income, cash_flow=cash_flow,
                         market=market_data, dividend=dividend, multi_year_deducted_profits=[30, 25, 20])


class TestScoringRegression(unittest.TestCase):
    def test_discrete_mode_backward_compatible(self):
        config = ScoringConfig(
            asset_continuous=AssetCushionContinuousConfig(enabled=False),
            operation_continuous=OperationSafetyContinuousConfig(enabled=False),
            redemption_continuous=RedemptionSafetyContinuousConfig(enabled=False),
            tie_break=TieBreakConfig(enabled=False),
        )
        scorer = Scorer(config)
        stock = _make_stock()
        ac = AssetCushionAnalyzer(AssetCushionConfig())
        op = OperationSafetyAnalyzer(OperationSafetyConfig())
        rd = RedemptionSafetyAnalyzer(RedemptionSafetyConfig())

        asset_result = ac.calculate(stock)
        op_result = op.evaluate(stock)
        rd_result = rd.evaluate(stock)

        scored = scorer.score(stock, asset_result, op_result, rd_result)

        self.assertEqual(scored.scoring_mode, "discrete")
        self.assertEqual(scored.asset_continuous_bonus, 0.0)
        self.assertEqual(scored.operation_continuous_adjustment, 0.0)
        self.assertEqual(scored.redemption_continuous_bonus, 0.0)

    def test_continuous_mode_improves_differentiation(self):
        config_discrete = ScoringConfig(
            asset_continuous=AssetCushionContinuousConfig(enabled=False),
            operation_continuous=OperationSafetyContinuousConfig(enabled=False),
            redemption_continuous=RedemptionSafetyContinuousConfig(enabled=False),
            tie_break=TieBreakConfig(enabled=False),
        )
        config_continuous = ScoringConfig()

        scorer_d = Scorer(config_discrete)
        scorer_c = Scorer(config_continuous)

        stock1 = _make_stock(code="A", cash=150, tca=250, tl=180, debt=40, mcap=800)
        stock2 = _make_stock(code="B", cash=80, tca=150, tl=120, debt=60, mcap=800)

        ac = AssetCushionAnalyzer(AssetCushionConfig())
        op = OperationSafetyAnalyzer(OperationSafetyConfig())
        rd = RedemptionSafetyAnalyzer(RedemptionSafetyConfig())

        discrete_scores = []
        continuous_scores = []
        for stock in [stock1, stock2]:
            ar = ac.calculate(stock)
            opr = op.evaluate(stock)
            rdr = rd.evaluate(stock)

            sd = scorer_d.score(stock, ar, opr, rdr)
            sc = scorer_c.score(stock, ar, opr, rdr,
                                asset_analyzer=ac, operation_analyzer=op, redemption_analyzer=rd)

            discrete_scores.append(sd.total_score)
            continuous_scores.append(sc.total_score)

        discrete_diff = abs(discrete_scores[0] - discrete_scores[1])
        continuous_diff = abs(continuous_scores[0] - continuous_scores[1])

        self.assertGreaterEqual(continuous_diff, discrete_diff)

    def test_continuous_mode_flag(self):
        config = ScoringConfig()
        scorer = Scorer(config)
        stock = _make_stock()
        ac = AssetCushionAnalyzer(AssetCushionConfig())
        op = OperationSafetyAnalyzer(OperationSafetyConfig())
        rd = RedemptionSafetyAnalyzer(RedemptionSafetyConfig())

        ar = ac.calculate(stock)
        opr = op.evaluate(stock)
        rdr = rd.evaluate(stock)

        scored = scorer.score(stock, ar, opr, rdr,
                              asset_analyzer=ac, operation_analyzer=op, redemption_analyzer=rd)
        self.assertEqual(scored.scoring_mode, "continuous")

    def test_tie_break_differentiates_equal_scores(self):
        config = ScoringConfig(
            asset_continuous=AssetCushionContinuousConfig(enabled=False),
            operation_continuous=OperationSafetyContinuousConfig(enabled=False),
            redemption_continuous=RedemptionSafetyContinuousConfig(enabled=False),
            tie_break=TieBreakConfig(enabled=True),
        )
        scorer = Scorer(config)

        stock1 = _make_stock(code="A", cash=200, tca=300, tl=150, na=400, mcap=1000)
        stock2 = _make_stock(code="B", cash=50, tca=100, tl=80, na=200, mcap=1000)

        ac = AssetCushionAnalyzer(AssetCushionConfig())
        op = OperationSafetyAnalyzer(OperationSafetyConfig())
        rd = RedemptionSafetyAnalyzer(RedemptionSafetyConfig())

        results = []
        for stock in [stock1, stock2]:
            ar = ac.calculate(stock)
            opr = op.evaluate(stock)
            rdr = rd.evaluate(stock)
            scored = scorer.score(stock, ar, opr, rdr)
            results.append(scored)

        self.assertNotEqual(results[0].tie_break_score, results[1].tie_break_score)

    def test_scores_bounded(self):
        config = ScoringConfig()
        scorer = Scorer(config)

        stock = _make_stock(cash=10000, tca=20000, tl=50, debt=10, mcap=100, div_yield=0.10, div_years=15)
        ac = AssetCushionAnalyzer(AssetCushionConfig())
        op = OperationSafetyAnalyzer(OperationSafetyConfig())
        rd = RedemptionSafetyAnalyzer(RedemptionSafetyConfig())

        ar = ac.calculate(stock)
        opr = op.evaluate(stock)
        rdr = rd.evaluate(stock)

        scored = scorer.score(stock, ar, opr, rdr,
                              asset_analyzer=ac, operation_analyzer=op, redemption_analyzer=rd)

        self.assertLessEqual(scored.asset_cushion_score, 100.0)
        self.assertLessEqual(scored.operation_safety_score, 100.0)
        self.assertLessEqual(scored.redemption_safety_score, 100.0)
        self.assertGreaterEqual(scored.asset_cushion_score, 0.0)
        self.assertGreaterEqual(scored.operation_safety_score, 0.0)
        self.assertGreaterEqual(scored.redemption_safety_score, 0.0)


if __name__ == "__main__":
    unittest.main()
