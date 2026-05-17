import math
import unittest

from common.continuous_mapping import linear_map, sigmoid_map, tanh_map, apply_mapping, normalize_to_range
from config.settings import ContinuousMappingConfig


class TestLinearMap(unittest.TestCase):
    def test_at_lower(self):
        self.assertAlmostEqual(linear_map(0.8, 0.8, 2.0, 10.0, 0.0), 0.0)

    def test_at_upper(self):
        self.assertAlmostEqual(linear_map(2.0, 0.8, 2.0, 10.0, 0.0), 10.0)

    def test_midpoint(self):
        result = linear_map(1.4, 0.8, 2.0, 10.0, 0.0)
        self.assertAlmostEqual(result, 5.0, places=1)

    def test_below_lower(self):
        result = linear_map(0.5, 0.8, 2.0, 10.0, 5.0)
        self.assertLess(result, 0.0)

    def test_above_upper(self):
        result = linear_map(3.0, 0.8, 2.0, 10.0, 5.0)
        self.assertEqual(result, 10.0)

    def test_equal_bounds(self):
        self.assertEqual(linear_map(0.5, 1.0, 1.0, 10.0, 5.0), 0.0)


class TestSigmoidMap(unittest.TestCase):
    def test_at_midpoint(self):
        result = sigmoid_map(1.4, 0.8, 2.0, 10.0, 0.0)
        self.assertAlmostEqual(result, 0.0, places=5)

    def test_at_upper(self):
        result = sigmoid_map(2.0, 0.8, 2.0, 10.0, 0.0)
        self.assertGreater(result, 0.0)
        self.assertLessEqual(result, 10.0)

    def test_at_lower(self):
        result = sigmoid_map(0.8, 0.8, 2.0, 10.0, 10.0)
        self.assertLess(result, 0.0)

    def test_bounded(self):
        result = sigmoid_map(100.0, 0.0, 1.0, 10.0, 10.0)
        self.assertLessEqual(result, 10.0)


class TestTanhMap(unittest.TestCase):
    def test_at_midpoint(self):
        result = tanh_map(1.4, 0.8, 2.0, 10.0, 0.0)
        self.assertAlmostEqual(result, 0.0, places=5)

    def test_symmetry(self):
        r1 = tanh_map(2.0, 0.8, 2.0, 10.0, 10.0)
        r2 = tanh_map(0.8, 0.8, 2.0, 10.0, 10.0)
        self.assertAlmostEqual(r1, -r2, places=5)

    def test_bounded(self):
        result = tanh_map(100.0, 0.0, 1.0, 10.0, 10.0)
        self.assertLessEqual(result, 10.0)


class TestApplyMapping(unittest.TestCase):
    def test_linear_dispatch(self):
        config = ContinuousMappingConfig(func_type="linear", lower_bound=0.0, upper_bound=1.0, max_bonus=10.0)
        result = apply_mapping(0.5, config)
        self.assertAlmostEqual(result, 5.0)

    def test_sigmoid_dispatch(self):
        config = ContinuousMappingConfig(func_type="sigmoid", lower_bound=0.0, upper_bound=1.0, max_bonus=10.0)
        result = apply_mapping(0.5, config)
        self.assertAlmostEqual(result, 0.0, places=3)

    def test_nan_handling(self):
        config = ContinuousMappingConfig()
        self.assertEqual(apply_mapping(float("nan"), config), 0.0)

    def test_inf_handling(self):
        config = ContinuousMappingConfig()
        self.assertEqual(apply_mapping(float("inf"), config), 0.0)

    def test_unknown_func_defaults_linear(self):
        config = ContinuousMappingConfig(func_type="unknown", lower_bound=0.0, upper_bound=1.0, max_bonus=10.0)
        result = apply_mapping(0.5, config)
        self.assertAlmostEqual(result, 5.0)


class TestNormalizeToRange(unittest.TestCase):
    def test_midpoint(self):
        result = normalize_to_range(0.5, 0.0, 1.0, 0.0, 100.0)
        self.assertAlmostEqual(result, 50.0)

    def test_boundary(self):
        result = normalize_to_range(0.0, 0.0, 1.0, 10.0, 20.0)
        self.assertAlmostEqual(result, 10.0)

    def test_equal_old_bounds(self):
        result = normalize_to_range(0.5, 1.0, 1.0, 0.0, 100.0)
        self.assertAlmostEqual(result, 50.0)


class TestContinuousScoring(unittest.TestCase):
    def test_asset_continuous_bonus_differentiates(self):
        from analyzer.asset_cushion import AssetCushionAnalyzer
        from config.settings import AssetCushionConfig, T0Config, T1Config, T2Config
        from common.models import AssetCushionResult, AssetCushionTier
        from config.settings import AssetCushionContinuousConfig

        config = AssetCushionConfig()
        analyzer = AssetCushionAnalyzer(config)
        cont_config = AssetCushionContinuousConfig()

        result1 = AssetCushionResult(conservative_ratio=0.85, loose_ratio=1.01, tier=AssetCushionTier.T1)
        result2 = AssetCushionResult(conservative_ratio=1.50, loose_ratio=2.00, tier=AssetCushionTier.T1)

        bonus1 = analyzer.calc_continuous_bonus(result1, cont_config)
        bonus2 = analyzer.calc_continuous_bonus(result2, cont_config)

        self.assertGreater(bonus2, bonus1)

    def test_operation_continuous_adjustment(self):
        from analyzer.operation_safety import OperationSafetyAnalyzer
        from config.settings import OperationSafetyConfig, OperationSafetyContinuousConfig
        from common.models import OperationSafetyResult, OperationStatus

        config = OperationSafetyConfig()
        analyzer = OperationSafetyAnalyzer(config)
        cont_config = OperationSafetyContinuousConfig()

        result_pass_low = OperationSafetyResult(free_cash_flow=100, capex_ratio=0.01, status=OperationStatus.PASS)
        result_pass_high = OperationSafetyResult(free_cash_flow=100, capex_ratio=0.49, status=OperationStatus.PASS)

        adj_low = analyzer.calc_continuous_adjustment(result_pass_low, cont_config)
        adj_high = analyzer.calc_continuous_adjustment(result_pass_high, cont_config)

        self.assertGreater(adj_low, adj_high)

    def test_redemption_continuous_score(self):
        from analyzer.redemption_safety import RedemptionSafetyAnalyzer
        from config.settings import RedemptionSafetyConfig, RedemptionSafetyContinuousConfig
        from common.models import RedemptionSafetyResult, StockFullData, StockInfo

        config = RedemptionSafetyConfig()
        analyzer = RedemptionSafetyAnalyzer(config)
        cont_config = RedemptionSafetyContinuousConfig()

        result_has = RedemptionSafetyResult(dividend_path=True, earnings_path=False, has_redemption_logic=True)
        result_none = RedemptionSafetyResult(has_redemption_logic=False)

        stock = StockFullData(info=StockInfo(code="00001", name="test"))

        score_has, _, _ = analyzer.calc_continuous_score(stock, result_has, cont_config)
        score_none, _, _ = analyzer.calc_continuous_score(stock, result_none, cont_config)

        self.assertGreater(score_has, score_none)
        self.assertGreater(score_has, 0.0)
        self.assertLessEqual(score_has, 100.0)


if __name__ == "__main__":
    unittest.main()
