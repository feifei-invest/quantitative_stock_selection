import os
from dataclasses import dataclass, field
from typing import Optional

import yaml

from common.exceptions import ConfigError


@dataclass
class DataSourceConfig:
    primary: str = "akshare"
    fallback: str = "baostock"
    max_attempts: int = 3
    interval_seconds: float = 5.0
    cache_enabled: bool = True
    cache_dir: str = "output_data/cache"
    finance_expire_hours: int = 4
    market_expire_hours: int = 1


@dataclass
class DelistingConfig:
    st_keywords: list = field(default_factory=lambda: ["ST", "*ST"])
    min_revenue: float = 100000000.0
    require_positive_net_assets: bool = True


@dataclass
class T0Config:
    min_conservative_ratio: float = 0.8
    min_loose_ratio: float = 1.5


@dataclass
class T1Config:
    min_loose_ratio: float = 1.0
    require_positive_conservative: bool = True


@dataclass
class T2Config:
    require_positive_loose: bool = True
    min_current_asset_net_ratio: float = 0.5


@dataclass
class AssetCushionConfig:
    t0: T0Config = field(default_factory=T0Config)
    t1: T1Config = field(default_factory=T1Config)
    t2: T2Config = field(default_factory=T2Config)


@dataclass
class OperationSafetyConfig:
    require_positive_fcf: bool = True
    max_capex_ratio: float = 0.5


@dataclass
class DividendConfig:
    min_years: int = 3
    min_dividend_yield: float = 0.02


@dataclass
class EarningsRecoveryConfig:
    lookback_years: int = 3


@dataclass
class RedemptionSafetyConfig:
    dividend: DividendConfig = field(default_factory=DividendConfig)
    earnings_recovery: EarningsRecoveryConfig = field(default_factory=EarningsRecoveryConfig)


@dataclass
class ContinuousMappingConfig:
    func_type: str = "linear"
    coefficient: float = 1.0
    lower_bound: float = 0.0
    upper_bound: float = 1.0
    max_bonus: float = 10.0
    max_penalty: float = 10.0


@dataclass
class AssetCushionContinuousConfig:
    conservative_ratio_mapping: ContinuousMappingConfig = field(default_factory=lambda: ContinuousMappingConfig(lower_bound=0.8, upper_bound=2.0, max_bonus=10.0, max_penalty=0.0))
    loose_ratio_mapping: ContinuousMappingConfig = field(default_factory=lambda: ContinuousMappingConfig(lower_bound=1.0, upper_bound=3.0, max_bonus=10.0, max_penalty=0.0))
    enabled: bool = True


@dataclass
class OperationSafetyContinuousConfig:
    capex_ratio_mapping: ContinuousMappingConfig = field(default_factory=lambda: ContinuousMappingConfig(lower_bound=0.0, upper_bound=0.5, max_bonus=15.0, max_penalty=15.0))
    enabled: bool = True


@dataclass
class RedemptionSafetyContinuousConfig:
    dividend_yield_weight: float = 0.4
    dividend_years_weight: float = 0.3
    earnings_recovery_weight: float = 0.3
    dividend_yield_mapping: ContinuousMappingConfig = field(default_factory=lambda: ContinuousMappingConfig(func_type="sigmoid", coefficient=2.0, lower_bound=0.02, upper_bound=0.08, max_bonus=20.0, max_penalty=0.0))
    dividend_years_mapping: ContinuousMappingConfig = field(default_factory=lambda: ContinuousMappingConfig(lower_bound=3.0, upper_bound=10.0, max_bonus=15.0, max_penalty=0.0))
    earnings_recovery_mapping: ContinuousMappingConfig = field(default_factory=lambda: ContinuousMappingConfig(lower_bound=0.0, upper_bound=1.0, max_bonus=15.0, max_penalty=0.0))
    base_pass_score: float = 60.0
    base_fail_score: float = 0.0
    enabled: bool = True


@dataclass
class TieBreakConfig:
    enabled: bool = True
    factors: list = field(default_factory=lambda: ["conservative_ratio", "loose_ratio", "dividend_yield"])
    factor_weights: list = field(default_factory=lambda: [0.4, 0.3, 0.3])


@dataclass
class ScoringConfig:
    asset_cushion_weight: float = 0.4
    operation_safety_weight: float = 0.3
    redemption_safety_weight: float = 0.3
    t0_score: float = 100.0
    t1_score: float = 70.0
    t2_score: float = 40.0
    fail_score: float = 0.0
    operation_pass_score: float = 100.0
    operation_partial_score: float = 50.0
    operation_fail_score: float = 0.0
    redemption_pass_score: float = 100.0
    redemption_fail_score: float = 0.0
    asset_continuous: AssetCushionContinuousConfig = field(default_factory=AssetCushionContinuousConfig)
    operation_continuous: OperationSafetyContinuousConfig = field(default_factory=OperationSafetyContinuousConfig)
    redemption_continuous: RedemptionSafetyContinuousConfig = field(default_factory=RedemptionSafetyContinuousConfig)
    tie_break: TieBreakConfig = field(default_factory=TieBreakConfig)


@dataclass
class OutputConfig:
    csv_dir: str = "output_data/results"
    csv_encoding: str = "utf-8-sig"
    log_dir: str = "logs"
    log_level: str = "INFO"
    terminal_max_rows: int = 50


@dataclass
class HKDataSourceConfig:
    primary: str = "akshare"
    fallback: str = "eastmoney"


@dataclass
class HKConstituentsConfig:
    include_sse: bool = True
    include_szse: bool = True
    max_stocks: int = 300


@dataclass
class HKCurrencyConfig:
    unit: str = "HKD"
    convert_to_cny: bool = False
    fixed_hkd_cny_rate: float = 0.0


@dataclass
class HKDelistingConfig:
    max_suspend_months: int = 3
    min_market_cap_hkd: float = 50000000.0
    filter_audit_opinion: bool = True


@dataclass
class HKStockConfig:
    data_source: HKDataSourceConfig = field(default_factory=HKDataSourceConfig)
    constituents: HKConstituentsConfig = field(default_factory=HKConstituentsConfig)
    currency: HKCurrencyConfig = field(default_factory=HKCurrencyConfig)
    delisting: HKDelistingConfig = field(default_factory=HKDelistingConfig)
    asset_cushion: Optional[AssetCushionConfig] = None
    scoring: Optional[ScoringConfig] = None
    field_mapping_path: str = "config/hk_field_mapping.yaml"


@dataclass
class Settings:
    data_source: DataSourceConfig = field(default_factory=DataSourceConfig)
    delisting: DelistingConfig = field(default_factory=DelistingConfig)
    asset_cushion: AssetCushionConfig = field(default_factory=AssetCushionConfig)
    operation_safety: OperationSafetyConfig = field(default_factory=OperationSafetyConfig)
    redemption_safety: RedemptionSafetyConfig = field(default_factory=RedemptionSafetyConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    market: str = "ALL"
    hk_stock: HKStockConfig = field(default_factory=HKStockConfig)

    _instance: Optional["Settings"] = field(default=None, repr=False)

    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "Settings":
        raw = cls._read_yaml(config_path)
        settings = cls._build_settings(raw)
        cls._validate(settings)
        Settings._instance = settings
        return settings

    @classmethod
    def get(cls) -> "Settings":
        if cls._instance is None:
            return cls.load()
        return cls._instance

    @classmethod
    def _read_yaml(cls, config_path: str) -> dict:
        default_path = os.path.join("config", "default_config.yaml")
        for path in [config_path, default_path]:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
        raise ConfigError(f"配置文件不存在: {config_path} 及 {default_path}")

    @classmethod
    def _build_settings(cls, raw: dict) -> "Settings":
        ds = raw.get("data_source", {})
        retry = ds.get("retry", {})
        cache = ds.get("cache", {})

        ac_raw = raw.get("asset_cushion", {})
        t0_raw = ac_raw.get("t0", {})
        t1_raw = ac_raw.get("t1", {})
        t2_raw = ac_raw.get("t2", {})

        rs_raw = raw.get("redemption_safety", {})
        div_raw = rs_raw.get("dividend", {})
        er_raw = rs_raw.get("earnings_recovery", {})

        sc_raw = raw.get("scoring", {})
        weights = sc_raw.get("weights", {})
        scores = sc_raw.get("scores", {})
        cont_raw = sc_raw.get("continuous", {})

        out_raw = raw.get("output", {})

        settings = cls(
            data_source=DataSourceConfig(
                primary=ds.get("primary", "akshare"),
                fallback=ds.get("fallback", "baostock"),
                max_attempts=retry.get("max_attempts", 3),
                interval_seconds=retry.get("interval_seconds", 5.0),
                cache_enabled=cache.get("enabled", True),
                cache_dir=cache.get("cache_dir", "output_data/cache"),
                finance_expire_hours=cache.get("finance_expire_hours", 4),
                market_expire_hours=cache.get("market_expire_hours", 1),
            ),
            delisting=DelistingConfig(
                st_keywords=raw.get("delisting", {}).get("st_keywords", ["ST", "*ST"]),
                min_revenue=raw.get("delisting", {}).get("min_revenue", 100000000.0),
                require_positive_net_assets=raw.get("delisting", {}).get("require_positive_net_assets", True),
            ),
            asset_cushion=AssetCushionConfig(
                t0=T0Config(
                    min_conservative_ratio=t0_raw.get("min_conservative_ratio", 0.8),
                    min_loose_ratio=t0_raw.get("min_loose_ratio", 1.5),
                ),
                t1=T1Config(
                    min_loose_ratio=t1_raw.get("min_loose_ratio", 1.0),
                    require_positive_conservative=t1_raw.get("require_positive_conservative", True),
                ),
                t2=T2Config(
                    require_positive_loose=t2_raw.get("require_positive_loose", True),
                    min_current_asset_net_ratio=t2_raw.get("min_current_asset_net_ratio", 0.5),
                ),
            ),
            operation_safety=OperationSafetyConfig(
                require_positive_fcf=raw.get("operation_safety", {}).get("require_positive_fcf", True),
                max_capex_ratio=raw.get("operation_safety", {}).get("max_capex_ratio", 0.5),
            ),
            redemption_safety=RedemptionSafetyConfig(
                dividend=DividendConfig(
                    min_years=div_raw.get("min_years", 3),
                    min_dividend_yield=div_raw.get("min_dividend_yield", 0.02),
                ),
                earnings_recovery=EarningsRecoveryConfig(
                    lookback_years=er_raw.get("lookback_years", 3),
                ),
            ),
            scoring=ScoringConfig(
                asset_cushion_weight=weights.get("asset_cushion", 0.4),
                operation_safety_weight=weights.get("operation_safety", 0.3),
                redemption_safety_weight=weights.get("redemption_safety", 0.3),
                t0_score=scores.get("t0", 100),
                t1_score=scores.get("t1", 70),
                t2_score=scores.get("t2", 40),
                fail_score=scores.get("fail", 0),
                operation_pass_score=scores.get("operation_pass", 100),
                operation_partial_score=scores.get("operation_partial", 50),
                operation_fail_score=scores.get("operation_fail", 0),
                redemption_pass_score=scores.get("redemption_pass", 100),
                redemption_fail_score=scores.get("redemption_fail", 0),
                asset_continuous=cls._build_asset_continuous(cont_raw.get("asset_cushion", {})),
                operation_continuous=cls._build_operation_continuous(cont_raw.get("operation_safety", {})),
                redemption_continuous=cls._build_redemption_continuous(cont_raw.get("redemption_safety", {})),
                tie_break=cls._build_tie_break(sc_raw.get("tie_break", {})),
            ),
            output=OutputConfig(
                csv_dir=out_raw.get("csv_dir", "output_data/results"),
                csv_encoding=out_raw.get("csv_encoding", "utf-8-sig"),
                log_dir=out_raw.get("log_dir", "logs"),
                log_level=out_raw.get("log_level", "INFO"),
                terminal_max_rows=out_raw.get("terminal_max_rows", 50),
            ),
            market=raw.get("market", "ALL"),
            hk_stock=cls._build_hk_stock(raw.get("hk_stock", {})),
        )
        return settings

    @classmethod
    def _build_hk_stock(cls, hk_raw: dict) -> HKStockConfig:
        ds = hk_raw.get("data_source", {})
        cons = hk_raw.get("constituents", {})
        cur = hk_raw.get("currency", {})
        dl = hk_raw.get("delisting", {})

        ac_raw = hk_raw.get("asset_cushion")
        hk_ac = None
        if ac_raw:
            hk_ac = AssetCushionConfig(
                t0=T0Config(
                    min_conservative_ratio=ac_raw.get("t0", {}).get("min_conservative_ratio", 0.8),
                    min_loose_ratio=ac_raw.get("t0", {}).get("min_loose_ratio", 1.5),
                ),
                t1=T1Config(
                    min_loose_ratio=ac_raw.get("t1", {}).get("min_loose_ratio", 1.0),
                    require_positive_conservative=ac_raw.get("t1", {}).get("require_positive_conservative", True),
                ),
                t2=T2Config(
                    require_positive_loose=ac_raw.get("t2", {}).get("require_positive_loose", True),
                    min_current_asset_net_ratio=ac_raw.get("t2", {}).get("min_current_asset_net_ratio", 0.5),
                ),
            )

        sc_raw = hk_raw.get("scoring")
        hk_sc = None
        if sc_raw:
            weights = sc_raw.get("weights", {})
            scores = sc_raw.get("scores", {})
            hk_sc = ScoringConfig(
                asset_cushion_weight=weights.get("asset_cushion", 0.4),
                operation_safety_weight=weights.get("operation_safety", 0.3),
                redemption_safety_weight=weights.get("redemption_safety", 0.3),
                t0_score=scores.get("t0", 100),
                t1_score=scores.get("t1", 70),
                t2_score=scores.get("t2", 40),
                fail_score=scores.get("fail", 0),
                operation_pass_score=scores.get("operation_pass", 100),
                operation_partial_score=scores.get("operation_partial", 50),
                operation_fail_score=scores.get("operation_fail", 0),
                redemption_pass_score=scores.get("redemption_pass", 100),
                redemption_fail_score=scores.get("redemption_fail", 0),
            )

        return HKStockConfig(
            data_source=HKDataSourceConfig(
                primary=ds.get("primary", "akshare"),
                fallback=ds.get("fallback", "eastmoney"),
            ),
            constituents=HKConstituentsConfig(
                include_sse=cons.get("include_sse", True),
                include_szse=cons.get("include_szse", True),
                max_stocks=cons.get("max_stocks", 300),
            ),
            currency=HKCurrencyConfig(
                unit=cur.get("unit", "HKD"),
                convert_to_cny=cur.get("convert_to_cny", False),
                fixed_hkd_cny_rate=cur.get("fixed_hkd_cny_rate", 0.0),
            ),
            delisting=HKDelistingConfig(
                max_suspend_months=dl.get("max_suspend_months", 3),
                min_market_cap_hkd=dl.get("min_market_cap_hkd", 50000000.0),
                filter_audit_opinion=dl.get("filter_audit_opinion", True),
            ),
            asset_cushion=hk_ac,
            scoring=hk_sc,
            field_mapping_path=hk_raw.get("field_mapping_path", "config/hk_field_mapping.yaml"),
        )

    @classmethod
    def _build_mapping_config(cls, raw: dict) -> ContinuousMappingConfig:
        return ContinuousMappingConfig(
            func_type=raw.get("func_type", "linear"),
            coefficient=raw.get("coefficient", 1.0),
            lower_bound=raw.get("lower_bound", 0.0),
            upper_bound=raw.get("upper_bound", 1.0),
            max_bonus=raw.get("max_bonus", 10.0),
            max_penalty=raw.get("max_penalty", 10.0),
        )

    @classmethod
    def _build_asset_continuous(cls, raw: dict) -> AssetCushionContinuousConfig:
        return AssetCushionContinuousConfig(
            conservative_ratio_mapping=cls._build_mapping_config(raw.get("conservative_ratio_mapping", {})),
            loose_ratio_mapping=cls._build_mapping_config(raw.get("loose_ratio_mapping", {})),
            enabled=raw.get("enabled", True),
        )

    @classmethod
    def _build_operation_continuous(cls, raw: dict) -> OperationSafetyContinuousConfig:
        return OperationSafetyContinuousConfig(
            capex_ratio_mapping=cls._build_mapping_config(raw.get("capex_ratio_mapping", {})),
            enabled=raw.get("enabled", True),
        )

    @classmethod
    def _build_redemption_continuous(cls, raw: dict) -> RedemptionSafetyContinuousConfig:
        return RedemptionSafetyContinuousConfig(
            dividend_yield_weight=raw.get("dividend_yield_weight", 0.4),
            dividend_years_weight=raw.get("dividend_years_weight", 0.3),
            earnings_recovery_weight=raw.get("earnings_recovery_weight", 0.3),
            dividend_yield_mapping=cls._build_mapping_config(raw.get("dividend_yield_mapping", {})),
            dividend_years_mapping=cls._build_mapping_config(raw.get("dividend_years_mapping", {})),
            earnings_recovery_mapping=cls._build_mapping_config(raw.get("earnings_recovery_mapping", {})),
            base_pass_score=raw.get("base_pass_score", 60.0),
            base_fail_score=raw.get("base_fail_score", 0.0),
            enabled=raw.get("enabled", True),
        )

    @classmethod
    def _build_tie_break(cls, raw: dict) -> TieBreakConfig:
        return TieBreakConfig(
            enabled=raw.get("enabled", True),
            factors=raw.get("factors", ["conservative_ratio", "loose_ratio", "dividend_yield"]),
            factor_weights=raw.get("factor_weights", [0.4, 0.3, 0.3]),
        )

    @classmethod
    def _validate(cls, settings: "Settings"):
        sc = settings.scoring
        total_weight = sc.asset_cushion_weight + sc.operation_safety_weight + sc.redemption_safety_weight
        if abs(total_weight - 1.0) > 0.01:
            raise ConfigError(f"评分权重之和应为1.0, 当前为{total_weight:.2f}")
