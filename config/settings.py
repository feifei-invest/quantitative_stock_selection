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


@dataclass
class OutputConfig:
    csv_dir: str = "output_data/results"
    csv_encoding: str = "utf-8-sig"
    log_dir: str = "logs"
    log_level: str = "INFO"
    terminal_max_rows: int = 50


@dataclass
class Settings:
    data_source: DataSourceConfig = field(default_factory=DataSourceConfig)
    delisting: DelistingConfig = field(default_factory=DelistingConfig)
    asset_cushion: AssetCushionConfig = field(default_factory=AssetCushionConfig)
    operation_safety: OperationSafetyConfig = field(default_factory=OperationSafetyConfig)
    redemption_safety: RedemptionSafetyConfig = field(default_factory=RedemptionSafetyConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

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
            ),
            output=OutputConfig(
                csv_dir=out_raw.get("csv_dir", "output_data/results"),
                csv_encoding=out_raw.get("csv_encoding", "utf-8-sig"),
                log_dir=out_raw.get("log_dir", "logs"),
                log_level=out_raw.get("log_level", "INFO"),
                terminal_max_rows=out_raw.get("terminal_max_rows", 50),
            ),
        )
        return settings

    @classmethod
    def _validate(cls, settings: "Settings"):
        sc = settings.scoring
        total_weight = sc.asset_cushion_weight + sc.operation_safety_weight + sc.redemption_safety_weight
        if abs(total_weight - 1.0) > 0.01:
            raise ConfigError(f"评分权重之和应为1.0, 当前为{total_weight:.2f}")
