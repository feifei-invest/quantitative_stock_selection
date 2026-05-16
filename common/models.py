from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AssetCushionTier(Enum):
    T0 = "T0"
    T1 = "T1"
    T2 = "T2"
    FAIL = "FAIL"


class OperationStatus(Enum):
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"


class RedemptionPath(Enum):
    DIVIDEND = "DIVIDEND"
    EVENT = "EVENT"
    EARNINGS_RECOVERY = "EARNINGS_RECOVERY"
    NONE = "NONE"


@dataclass
class StockInfo:
    code: str = ""
    name: str = ""
    exchange: str = ""
    market: str = "A"


@dataclass
class BalanceSheet:
    cash_and_equivalents: float = 0.0
    total_current_assets: float = 0.0
    total_assets: float = 0.0
    total_current_liabilities: float = 0.0
    total_liabilities: float = 0.0
    interest_bearing_debt: float = 0.0
    net_assets: float = 0.0


@dataclass
class IncomeStatement:
    revenue: float = 0.0
    operating_cost: float = 0.0
    net_profit: float = 0.0
    deducted_net_profit: float = 0.0


@dataclass
class CashFlowStatement:
    operating_cash_flow: float = 0.0
    capital_expenditure: float = 0.0
    free_cash_flow: float = 0.0


@dataclass
class MarketData:
    total_market_cap: float = 0.0
    circulating_market_cap: float = 0.0
    latest_price: float = 0.0


@dataclass
class DividendData:
    total_cash_dividend_3y: float = 0.0
    dividend_yield: float = 0.0
    dividend_years: int = 0


@dataclass
class StockFullData:
    info: StockInfo = field(default_factory=StockInfo)
    balance: BalanceSheet = field(default_factory=BalanceSheet)
    income: IncomeStatement = field(default_factory=IncomeStatement)
    cash_flow: CashFlowStatement = field(default_factory=CashFlowStatement)
    market: MarketData = field(default_factory=MarketData)
    dividend: DividendData = field(default_factory=DividendData)
    multi_year_deducted_profits: list = field(default_factory=list)
    is_data_complete: bool = True
    missing_fields: list = field(default_factory=list)


@dataclass
class AssetCushionResult:
    conservative_cash_net: float = 0.0
    loose_cash_net: float = 0.0
    conservative_ratio: float = 0.0
    loose_ratio: float = 0.0
    current_asset_net_ratio: float = 0.0
    tier: AssetCushionTier = AssetCushionTier.FAIL


@dataclass
class OperationSafetyResult:
    free_cash_flow: float = 0.0
    capex_ratio: float = 0.0
    is_fcf_positive: bool = False
    is_capex_ratio_low: bool = False
    status: OperationStatus = OperationStatus.FAIL


@dataclass
class RedemptionSafetyResult:
    dividend_path: bool = False
    event_path: bool = False
    earnings_path: bool = False
    has_redemption_logic: bool = False
    path_type: RedemptionPath = RedemptionPath.NONE


@dataclass
class ScoredResult:
    stock_code: str = ""
    stock_name: str = ""
    asset_cushion_tier: str = "FAIL"
    conservative_ratio: float = 0.0
    loose_ratio: float = 0.0
    free_cash_flow: float = 0.0
    capex_ratio: float = 0.0
    redemption_path_type: str = "NONE"
    asset_cushion_score: float = 0.0
    operation_safety_score: float = 0.0
    redemption_safety_score: float = 0.0
    total_score: float = 0.0
    rank: int = 0
    market: str = "A"
    currency: str = "CNY"
    deducted_net_profit_is_estimated: bool = False
