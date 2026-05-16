# 沪深300价值股票量化选股系统 — 技术设计文档

---

# **1. 实现模型**

## **1.1 上下文视图**

### 系统上下文图

```
┌─────────────────────────────────────────────────────────────┐
│                     外部数据源                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ akshare  │  │ tushare  │  │ baostock │                  │
│  │ (主数据源)│  │ (备选1)  │  │ (备选2)  │                  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
│       │              │              │                        │
└───────┼──────────────┼──────────────┼────────────────────────┘
        │              │              │
        ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│              沪深300价值选股系统（本系统）                     │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 数据获取层│→│ 业务逻辑层│→│ 输出展示层│  │ 配置管理  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
       ┌────────────┐         ┌────────────┐
       │ CSV 文件   │         │ 终端表格   │
       └────────────┘         └────────────┘
```

### 上下文说明

| 外部实体 | 交互方式 | 对应需求 |
|----------|----------|----------|
| akshare | Python API调用，免费无Token | CON-002, CON-004 |
| tushare | Python API调用，需Token（备选） | CON-002 |
| baostock | Python API调用，免费（备选） | CON-002 |
| CSV文件 | 本地文件写入 | REQ-015 |
| 终端 | 标准输出表格 | REQ-015 |
| YAML配置文件 | 本地文件读取 | NFR-004 |

## **1.2 服务/组件总体架构**

### 分层架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     入口层 (Entry)                           │
│                    main.py (CLI入口)                         │
├─────────────────────────────────────────────────────────────┤
│                   配置层 (Config)                            │
│              config.yaml + settings.py                       │
├─────────────────────────────────────────────────────────────┤
│                  数据获取层 (DataFetcher)                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │成分股获取器 │ │财务数据获取器│ │市值分红获取器│              │
│  └────────────┘ └────────────┘ └────────────┘              │
├─────────────────────────────────────────────────────────────┤
│                  业务逻辑层 (Analyzer)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │退市风险过滤│ │资产垫评估 │ │经营安全评估│ │兑现安全评估│     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│  ┌──────────┐                                              │
│  │综合评分  │                                              │
│  └──────────┘                                              │
├─────────────────────────────────────────────────────────────┤
│                  输出层 (Output)                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐             │
│  │ CSV 输出器  │ │表格输出器  │ │ 日志记录器  │             │
│  └────────────┘ └────────────┘ └────────────┘             │
├─────────────────────────────────────────────────────────────┤
│                  公共层 (Common)                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐             │
│  │ 数据模型   │ │ 重试/异常  │ │ 缓存管理   │             │
│  └────────────┘ └────────────┘ └────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

### 项目目录结构

```
quantitative_stock_selection/
├── main.py                          # 主入口，流程编排
├── config.yaml                      # 指标阈值与运行参数配置
├── requirements.txt                 # Python依赖清单
├── README.md                        # 项目说明（可选）
│
├── config/                          # 配置管理模块
│   ├── __init__.py
│   ├── settings.py                  # 配置加载与校验
│   └── default_config.yaml          # 默认配置模板
│
├── fetcher/                         # 数据获取层
│   ├── __init__.py
│   ├── base_fetcher.py              # 数据获取基类（含重试机制）
│   ├── index_fetcher.py             # 沪深300成分股获取 (REQ-001)
│   ├── finance_fetcher.py           # 财务数据获取 (REQ-002)
│   ├── market_fetcher.py            # 市值数据获取 (REQ-003)
│   ├── dividend_fetcher.py          # 分红数据获取 (REQ-004)
│   └── data_cache.py               # 数据缓存管理 (NFR-001)
│
├── analyzer/                        # 业务逻辑层
│   ├── __init__.py
│   ├── delisting_filter.py          # 退市风险过滤 (REQ-013)
│   ├── asset_cushion.py             # 资产垫计算与分级 (REQ-005, REQ-006)
│   ├── operation_safety.py          # 经营安全评估 (REQ-007, REQ-008)
│   ├── redemption_safety.py         # 兑现安全评估 (REQ-009, REQ-010)
│   └── scorer.py                    # 综合评分与排序 (REQ-011, REQ-012)
│
├── output/                          # 输出层
│   ├── __init__.py
│   ├── csv_writer.py                # CSV文件输出 (REQ-015)
│   ├── table_printer.py             # 终端表格输出 (REQ-015)
│   └── formatter.py                 # 数据格式化工具
│
├── common/                          # 公共层
│   ├── __init__.py
│   ├── models.py                    # 数据模型定义 (dataclass)
│   ├── logger.py                    # 日志管理 (NFR-003)
│   ├── retry.py                     # 重试装饰器 (NFR-002)
│   └── exceptions.py                # 自定义异常
│
├── output_data/                     # 输出数据目录
│   └── results/                     # CSV结果文件存放
│
├── logs/                            # 日志文件目录
│
└── tests/                           # 单元测试
    ├── __init__.py
    ├── test_asset_cushion.py
    ├── test_operation_safety.py
    ├── test_redemption_safety.py
    ├── test_scorer.py
    └── test_delisting_filter.py
```

## **1.3 实现设计文档**

### 1.3.1 配置管理模块

#### 设计目标
- 对应需求：NFR-004（指标阈值可通过配置文件调整）
- 对应需求：CON-002（数据源优先级可配置）

#### 配置文件结构 (config.yaml)

```yaml
# 数据源配置
data_source:
  primary: akshare           # 主数据源
  fallback: [tushare, baostock]  # 备选数据源列表
  retry:
    max_attempts: 3          # 最大重试次数 (NFR-002)
    interval_seconds: 5      # 重试间隔秒数 (NFR-002)
  cache:
    enabled: true            # 是否启用缓存
    expire_hours: 4          # 缓存过期时间（小时）
    cache_dir: "./.cache"    # 缓存目录

# 退市风险过滤阈值 (REQ-013)
delisting:
  st_keywords: ["ST", "*ST"]         # ST风险关键词
  min_revenue: 100000000             # 最低营业收入（1亿元）
  require_positive_net_assets: true  # 净资产必须为正

# 资产垫分级阈值 (REQ-005, REQ-006)
asset_cushion:
  t0:
    conservative_ratio: 0.8          # 保守现金净额/市值 >= 0.8
    loose_ratio: 1.5                 # 宽松现金净额/市值 >= 1.5
  t1:
    loose_ratio: 1.0                 # 宽松现金净额/市值 >= 1.0
    require_conservative_positive: true  # 保守现金净额 > 0
  t2:
    require_loose_positive: true     # 宽松现金净额 > 0
    current_asset_ratio: 0.5         # (流动资产-总负债)/市值 > 0.5

# 经营安全阈值 (REQ-007, REQ-008)
operation_safety:
  require_positive_fcf: true         # 自由现金流 > 0
  max_capex_ratio: 0.5              # 资本开支率 < 0.5

# 兑现安全阈值 (REQ-009, REQ-010)
redemption_safety:
  dividend:
    min_years: 3                     # 最少分红年数
    min_avg_yield: 0.02              # 平均股息率 > 2%
  earnings_recovery:
    min_years: 3                     # 最少考察年数
    require_all_positive: true       # 所有年份扣非净利润为正
    require_increasing: true         # 最近年 > 前年

# 综合评分权重 (REQ-011)
scoring:
  asset_cushion_weight: 0.40         # 资产垫权重 40%
  operation_safety_weight: 0.30      # 经营安全权重 30%
  redemption_safety_weight: 0.30     # 兑现安全权重 30%
  asset_cushion_scores:
    t0: 100
    t1: 70
    t2: 40
    fail: 0
  operation_safety_scores:
    pass: 100                        # FCF>0 且 capex_ratio<0.5
    partial: 50                      # 部分满足
    fail: 0                          # 不满足
  redemption_safety_scores:
    pass: 100
    fail: 0

# 输出配置 (REQ-014, REQ-015)
output:
  csv_dir: "./output_data/results"
  csv_encoding: "utf-8-sig"         # CSV编码（Excel兼容中文）
  log_dir: "./logs"
  log_level: "INFO"
  terminal_max_rows: 50              # 终端表格最大显示行数
```

#### 核心类设计

```python
# config/settings.py
@dataclass
class DataSourceConfig:
    primary: str
    fallback: list[str]
    retry_max_attempts: int
    retry_interval_seconds: int
    cache_enabled: bool
    cache_expire_hours: int
    cache_dir: str

@dataclass
class AssetCushionConfig:
    t0_conservative_ratio: float
    t0_loose_ratio: float
    t1_loose_ratio: float
    t1_require_conservative_positive: bool
    t2_require_loose_positive: bool
    t2_current_asset_ratio: float

@dataclass
class ScoringConfig:
    asset_cushion_weight: float
    operation_safety_weight: float
    redemption_safety_weight: float
    asset_cushion_scores: dict[str, int]
    operation_safety_scores: dict[str, int]
    redemption_safety_scores: dict[str, int]

class Settings:
    """全局配置单例，从config.yaml加载所有配置"""
    _instance: ClassVar["Settings | None"] = None

    data_source: DataSourceConfig
    delisting: DelistingConfig
    asset_cushion: AssetCushionConfig
    operation_safety: OperationSafetyConfig
    redemption_safety: RedemptionSafetyConfig
    scoring: ScoringConfig
    output: OutputConfig

    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "Settings": ...
    @classmethod
    def get(cls) -> "Settings": ...
```

---

### 1.3.2 数据获取层 (fetcher/)

#### 设计目标
- 对应需求：REQ-001（成分股获取）、REQ-002（财务数据）、REQ-003（市值数据）、REQ-004（分红数据）
- 对应需求：NFR-001（5分钟内完成）、NFR-002（重试机制）、NFR-005（数据缺失处理）
- 对应约束：CON-002（akshare优先）、CON-004（不使用付费接口）

#### 数据获取基类

```python
# fetcher/base_fetcher.py
class BaseFetcher(ABC):
    """数据获取基类，封装重试机制与异常处理"""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def fetch(self, *args, **kwargs) -> Any:
        """子类实现的实际获取逻辑"""
        ...

    def fetch_with_retry(self, *args, **kwargs) -> Any:
        """带重试机制的获取方法 (NFR-002)"""
        ...

    def _handle_data_missing(self, stock_code: str, field: str) -> None:
        """数据缺失处理：记录日志并标记 (NFR-005)"""
        ...
```

#### 沪深300成分股获取器 (REQ-001)

```python
# fetcher/index_fetcher.py
class IndexFetcher(BaseFetcher):
    """沪深300成分股获取"""

    def fetch_hs300_constituents(self) -> list[StockInfo]:
        """
        获取沪深300全部成分股代码及名称

        Returns:
            list[StockInfo]: 成分股列表，包含股票代码、名称、交易所

        数据源优先级:
            1. akshare: ak.index_stock_cs300()
            2. tushare: 需token (备选)
            3. baostock (备选)

        对应需求: REQ-001
        """
        ...
```

#### 财务数据获取器 (REQ-002)

```python
# fetcher/finance_fetcher.py
class FinanceFetcher(BaseFetcher):
    """上市公司财务数据获取"""

    def fetch_balance_sheet(self, stock_code: str) -> BalanceSheet:
        """
        获取资产负债表数据

        Returns:
            BalanceSheet: 包含以下字段
                - cash_and_equivalents: 现金及现金等价物
                - total_current_assets: 流动资产合计
                - total_assets: 总资产
                - total_current_liabilities: 流动负债合计
                - total_liabilities: 总负债
                - interest_bearing_debt: 有息负债(短期借款+长期借款+应付债券)
                - net_assets: 净资产(所有者权益合计)

        数据源: akshare stock_balance_sheet_by_report_em
        对应需求: REQ-002 (资产负债表部分)
        """
        ...

    def fetch_income_statement(self, stock_code: str) -> IncomeStatement:
        """
        获取利润表数据

        Returns:
            IncomeStatement: 包含以下字段
                - revenue: 营业收入
                - operating_cost: 营业成本
                - net_profit: 净利润
                - deducted_net_profit: 扣非净利润

        对应需求: REQ-002 (利润表部分)
        """
        ...

    def fetch_cash_flow(self, stock_code: str) -> CashFlowStatement:
        """
        获取现金流量表数据

        Returns:
            CashFlowStatement: 包含以下字段
                - operating_cash_flow: 经营活动现金流净额
                - capital_expenditure: 资本开支(购建固定资产等支付现金)
                - free_cash_flow: 自由现金流(经营现金流-资本开支)

        对应需求: REQ-002 (现金流量表部分)
        """
        ...

    def fetch_multi_year_deducted_profit(self, stock_code: str, years: int = 3) -> list[float]:
        """
        获取近N年扣非净利润，用于盈利恢复判断

        对应需求: REQ-010
        """
        ...
```

#### 市值数据获取器 (REQ-003)

```python
# fetcher/market_fetcher.py
class MarketFetcher(BaseFetcher):
    """市值与行情数据获取"""

    def fetch_market_data(self, stock_code: str) -> MarketData:
        """
        获取市值数据

        Returns:
            MarketData: 包含以下字段
                - total_market_cap: 总市值
                - circulating_market_cap: 流通市值
                - latest_price: 最新股价

        数据源: akshare stock_zh_a_spot_em (实时行情)
        对应需求: REQ-003
        """
        ...

    def fetch_batch_market_data(self, stock_codes: list[str]) -> dict[str, MarketData]:
        """
        批量获取市值数据（优化性能，单次请求全市场数据后过滤）

        对应需求: NFR-001 (性能优化)
        """
        ...
```

#### 分红数据获取器 (REQ-004)

```python
# fetcher/dividend_fetcher.py
class DividendFetcher(BaseFetcher):
    """分红数据获取"""

    def fetch_dividend_data(self, stock_code: str) -> DividendData:
        """
        获取分红数据

        Returns:
            DividendData: 包含以下字段
                - total_cash_dividend_3y: 近3年累计现金分红金额
                - dividend_yield: 股息率
                - dividend_years: 近3年分红年数

        数据源: akshare stock_dividend_cn
        对应需求: REQ-004
        """
        ...
```

#### 数据缓存管理 (NFR-001)

```python
# fetcher/data_cache.py
class DataCache:
    """
    基于磁盘的JSON缓存管理

    设计要点:
    - 缓存键: 由数据类型+股票代码+日期组成
    - 缓存格式: JSON文件
    - 过期策略: 按配置的expire_hours自动失效
    - 财务数据缓存期较长(季度更新)，行情数据缓存期短(日更)

    对应需求: NFR-001 (避免重复请求，提升性能)
    """

    def get(self, cache_key: str) -> dict | None: ...
    def set(self, cache_key: str, data: dict, expire_hours: int | None = None) -> None: ...
    def is_expired(self, cache_key: str) -> bool: ...
    def clear_all(self) -> None: ...
```

---

### 1.3.3 业务逻辑层 (analyzer/)

#### 退市风险过滤模块 (REQ-013)

```python
# analyzer/delisting_filter.py
class DelistingFilter:
    """
    退市风险过滤

    过滤规则 (REQ-013):
    1. 股票简称包含"ST"或"*ST"
    2. 最近一年扣非净利润为负 且 营业收入 < 1亿元
    3. 期末净资产为负值
    """

    def __init__(self, config: DelistingConfig): ...

    def is_delisting_risk(self, stock: StockFullData) -> bool:
        """
        判断是否存在退市风险

        Args:
            stock: 股票完整数据（含财务、市值）

        Returns:
            bool: True表示存在退市风险，应剔除

        对应需求: REQ-013
        """
        ...

    def filter(self, stocks: list[StockFullData]) -> list[StockFullData]:
        """
        批量过滤退市风险股

        Returns:
            过滤后的安全股票列表
        """
        ...

    def _check_st_status(self, stock_name: str) -> bool: ...
    def _check_financial_risk(self, deducted_profit: float, revenue: float) -> bool: ...
    def _check_negative_assets(self, net_assets: float) -> bool: ...
```

#### 资产垫计算与分级模块 (REQ-005, REQ-006)

```python
# analyzer/asset_cushion.py
class AssetCushionAnalyzer:
    """
    资产垫计算与分级

    核心公式 (REQ-005):
    - 现金净额(保守) = 现金及等价物 - 总负债
    - 现金净额(宽松) = 现金及等价物 - 有息负债
    - 资产垫比率(保守) = 现金净额(保守) / 总市值
    - 资产垫比率(宽松) = 现金净额(宽松) / 总市值

    分级规则 (REQ-006):
    - T0: 保守比率>=0.8 且 宽松比率>=1.5
    - T1: 宽松比率>=1.0 且 保守现金净额>0
    - T2: 宽松现金净额>0 且 (流动资产-总负债)/市值>0.5
    - 不符合: 不满足以上任何条件
    """

    def __init__(self, config: AssetCushionConfig): ...

    def calculate(self, stock: StockFullData) -> AssetCushionResult:
        """
        计算资产垫指标并分级

        Returns:
            AssetCushionResult: 包含
                - conservative_cash_net: 保守现金净额
                - loose_cash_net: 宽松现金净额
                - conservative_ratio: 保守资产垫比率
                - loose_ratio: 宽松资产垫比率
                - current_asset_net_ratio: 流动资产净值比率
                - tier: AssetCushionTier (T0/T1/T2/FAIL)

        对应需求: REQ-005, REQ-006
        """
        ...

    def _classify_tier(self, result: AssetCushionResult) -> AssetCushionTier: ...
```

#### 经营安全评估模块 (REQ-007, REQ-008)

```python
# analyzer/operation_safety.py
class OperationSafetyAnalyzer:
    """
    经营安全评估

    计算指标 (REQ-007):
    - 自由现金流 = 经营现金流 - 资本开支
    - 资本开支率 = 资本开支 / 经营现金流

    筛选条件 (REQ-008):
    - 自由现金流 > 0
    - 资本开支率 < 0.5
    """

    def __init__(self, config: OperationSafetyConfig): ...

    def evaluate(self, stock: StockFullData) -> OperationSafetyResult:
        """
        评估经营安全

        Returns:
            OperationSafetyResult: 包含
                - free_cash_flow: 自由现金流
                - capex_ratio: 资本开支率
                - is_fcf_positive: 自由现金流是否为正
                - is_capex_ratio_low: 资本开支率是否低于阈值
                - status: OperationStatus (PASS/PARTIAL/FAIL)

        对应需求: REQ-007, REQ-008
        """
        ...
```

#### 兑现安全评估模块 (REQ-009, REQ-010)

```python
# analyzer/redemption_safety.py
class RedemptionSafetyAnalyzer:
    """
    兑现安全评估

    三条兑现路径 (REQ-009):
    1. 分红兑现: 近3年持续分红 且 平均股息率>2%
    2. 事件兑现: 近1年存在资产处置/股权回购等特殊事件
    3. 盈利恢复兑现: 近3年扣非净利润为正且呈恢复趋势 (REQ-010)
    """

    def __init__(self, config: RedemptionSafetyConfig): ...

    def evaluate(self, stock: StockFullData) -> RedemptionSafetyResult:
        """
        评估兑现安全

        Returns:
            RedemptionSafetyResult: 包含
                - dividend_path: bool (分红兑现)
                - event_path: bool (事件兑现)
                - earnings_path: bool (盈利恢复兑现)
                - has_redemption_logic: bool (满足任一路径)
                - path_type: str (兑现路径描述)

        对应需求: REQ-009, REQ-010
        """
        ...

    def _check_dividend_path(self, dividend: DividendData) -> bool:
        """检查分红兑现路径"""
        ...

    def _check_event_path(self, stock_code: str) -> bool:
        """
        检查事件兑现路径

        注：由于事件数据获取难度较高且可靠数据源有限，
        初版实现中此路径默认返回False，
        后续可通过扩展akshare事件接口或人工标注补充。
        """
        ...

    def _check_earnings_path(self, deducted_profits: list[float]) -> bool:
        """
        检查盈利恢复兑现路径 (REQ-010)
        条件: 近3年扣非净利润均为正 且 最近年 > 前年
        """
        ...
```

#### 综合评分与排序模块 (REQ-011, REQ-012)

```python
# analyzer/scorer.py
class Scorer:
    """
    综合评分与排序

    评分规则 (REQ-011):
    - 资产垫得分(40%): T0=100, T1=70, T2=40, 不符合=0
    - 经营安全得分(30%): PASS=100, PARTIAL=50, FAIL=0
    - 兑现安全得分(30%): 有兑现逻辑=100, 无=0

    综合分 = 资产垫得分×40% + 经营安全得分×30% + 兑现安全得分×30%
    """

    def __init__(self, config: ScoringConfig): ...

    def score(self, stock: StockFullData,
              asset_result: AssetCushionResult,
              operation_result: OperationSafetyResult,
              redemption_result: RedemptionSafetyResult) -> ScoredResult:
        """
        计算综合评分

        Returns:
            ScoredResult: 包含
                - asset_cushion_score: 资产垫得分
                - operation_safety_score: 经营安全得分
                - redemption_safety_score: 兑现安全得分
                - total_score: 综合得分
                - rank: 排名（排序后设置）

        对应需求: REQ-011
        """
        ...

    def rank(self, results: list[ScoredResult]) -> list[ScoredResult]:
        """
        按综合得分从高到低排序

        对应需求: REQ-012
        """
        ...
```

---

### 1.3.4 输出层 (output/)

#### CSV输出器 (REQ-015)

```python
# output/csv_writer.py
class CsvWriter:
    """
    将选股结果写入CSV文件

    输出字段 (REQ-014):
    股票代码, 股票名称, 资产垫等级, 资产垫比率(保守), 资产垫比率(宽松),
    自由现金流, 资本开支率, 兑现逻辑类型, 资产垫得分, 经营安全得分,
    兑现安全得分, 综合评分, 排名
    """

    def __init__(self, output_dir: str, encoding: str = "utf-8-sig"): ...

    def write(self, results: list[ScoredResult], filename: str | None = None) -> str:
        """
        写入CSV文件

        Args:
            results: 排序后的评分结果
            filename: 可选指定文件名，默认按日期自动生成

        Returns:
            str: 写入的文件路径

        对应需求: REQ-015
        """
        ...
```

#### 终端表格输出器 (REQ-015)

```python
# output/table_printer.py
class TablePrinter:
    """
    终端表格输出

    使用 rich 库的 Table 组件实现美观的终端表格展示
    """

    def __init__(self, max_rows: int = 50): ...

    def print(self, results: list[ScoredResult]) -> None:
        """
        打印终端表格

        对应需求: REQ-015
        """
        ...
```

#### 日志记录器 (NFR-003)

```python
# common/logger.py
class LoggerManager:
    """
    日志管理

    配置:
    - 同时输出到终端和文件
    - 文件按日期命名
    - 日志级别可配置
    - 包含数据获取情况、筛选过程、异常信息

    对应需求: NFR-003
    """

    @staticmethod
    def setup(log_dir: str, log_level: str = "INFO") -> logging.Logger: ...
```

---

### 1.3.5 主流程编排 (main.py)

```python
# main.py
def main():
    """
    主流程编排

    完整执行流程:
    1. 加载配置 (config.yaml)
    2. 初始化日志
    3. 获取沪深300成分股 (REQ-001)
    4. 批量获取财务数据 (REQ-002, REQ-003, REQ-004)
    5. 退市风险过滤 (REQ-013)
    6. 逐股评估三要义:
       a. 资产垫计算与分级 (REQ-005, REQ-006)
       b. 经营安全评估 (REQ-007, REQ-008)
       c. 兑现安全评估 (REQ-009, REQ-010)
    7. 综合评分与排序 (REQ-011, REQ-012)
    8. 输出结果 (REQ-014, REQ-015)

    对应需求: NFR-001 (5分钟内完成), NFR-005 (数据缺失不中断)
    """

    # Step 1: 加载配置
    settings = Settings.load("config.yaml")

    # Step 2: 初始化日志
    logger = LoggerManager.setup(settings.output.log_dir, settings.output.log_level)

    # Step 3: 获取沪深300成分股
    index_fetcher = IndexFetcher(settings)
    constituents = index_fetcher.fetch_hs300_constituents()

    # Step 4: 批量获取数据
    finance_fetcher = FinanceFetcher(settings)
    market_fetcher = MarketFetcher(settings)
    dividend_fetcher = DividendFetcher(settings)

    stock_data_list: list[StockFullData] = []
    for stock_info in constituents:
        try:
            balance = finance_fetcher.fetch_balance_sheet(stock_info.code)
            income = finance_fetcher.fetch_income_statement(stock_info.code)
            cash_flow = finance_fetcher.fetch_cash_flow(stock_info.code)
            market = market_fetcher.fetch_market_data(stock_info.code)
            dividend = dividend_fetcher.fetch_dividend_data(stock_info.code)
            multi_year_profit = finance_fetcher.fetch_multi_year_deducted_profit(
                stock_info.code, years=3
            )
            stock_data = StockFullData(
                info=stock_info, balance=balance, income=income,
                cash_flow=cash_flow, market=market, dividend=dividend,
                multi_year_deducted_profits=multi_year_profit
            )
            stock_data_list.append(stock_data)
        except DataMissingError:
            logger.warning(f"数据不完整，跳过: {stock_info.code} {stock_info.name}")
            continue

    # Step 5: 退市风险过滤
    delisting_filter = DelistingFilter(settings.delisting)
    safe_stocks = delisting_filter.filter(stock_data_list)

    # Step 6-7: 逐股评估 + 综合评分
    asset_analyzer = AssetCushionAnalyzer(settings.asset_cushion)
    operation_analyzer = OperationSafetyAnalyzer(settings.operation_safety)
    redemption_analyzer = RedemptionSafetyAnalyzer(settings.redemption_safety)
    scorer = Scorer(settings.scoring)

    scored_results: list[ScoredResult] = []
    for stock in safe_stocks:
        asset_result = asset_analyzer.calculate(stock)
        operation_result = operation_analyzer.evaluate(stock)
        redemption_result = redemption_analyzer.evaluate(stock)
        result = scorer.score(stock, asset_result, operation_result, redemption_result)
        scored_results.append(result)

    # 排序
    ranked_results = scorer.rank(scored_results)

    # Step 8: 输出结果
    csv_writer = CsvWriter(settings.output.csv_dir)
    csv_path = csv_writer.write(ranked_results)

    table_printer = TablePrinter(settings.output.terminal_max_rows)
    table_printer.print(ranked_results)

    logger.info(f"选股完成，共 {len(ranked_results)} 只股票入选，结果已保存至 {csv_path}")


if __name__ == "__main__":
    main()
```

---

# **2. 接口设计**

## **2.1 总体设计**

### 接口分层原则

| 层次 | 调用方向 | 接口风格 |
|------|----------|----------|
| 数据获取层 → 外部API | 向上调用 | Python SDK调用（akshare/tushare/baostock） |
| 业务逻辑层 → 数据获取层 | 向下依赖 | Python函数调用，通过数据模型传参 |
| 输出层 → 业务逻辑层 | 向下依赖 | Python函数调用，接收ScoredResult列表 |
| 配置层 → 全局 | 横切关注点 | 全局单例Settings |

### 数据源接口映射表

| 数据项 | akshare接口 | 备选方案 | 对应需求 |
|--------|-------------|----------|----------|
| 沪深300成分股 | `ak.index_stock_cs300()` | tushare: `pro.index_weight()` | REQ-001 |
| 资产负债表 | `ak.stock_balance_sheet_by_report_em(symbol=code)` | tushare: `pro.balance()` | REQ-002 |
| 利润表 | `ak.stock_profit_sheet_by_report_em(symbol=code)` | tushare: `pro.income()` | REQ-002 |
| 现金流量表 | `ak.stock_cash_flow_statement_by_report_em(symbol=code)` | tushare: `pro.cashflow()` | REQ-002 |
| 实时行情/市值 | `ak.stock_zh_a_spot_em()` | tushare: `pro.daily_basic()` | REQ-003 |
| 分红数据 | `ak.stock_dividend_cn(symbol=code)` | tushare: `pro.dividend()` | REQ-004 |

## **2.2 接口清单**

### 数据获取层接口

| 接口名称 | 所属模块 | 签名 | 输入 | 输出 | 对应需求 |
|----------|----------|------|------|------|----------|
| 获取成分股 | IndexFetcher | `fetch_hs300_constituents() -> list[StockInfo]` | 无 | 成分股列表 | REQ-001 |
| 获取资产负债表 | FinanceFetcher | `fetch_balance_sheet(code: str) -> BalanceSheet` | 股票代码 | 资产负债表数据 | REQ-002 |
| 获取利润表 | FinanceFetcher | `fetch_income_statement(code: str) -> IncomeStatement` | 股票代码 | 利润表数据 | REQ-002 |
| 获取现金流量表 | FinanceFetcher | `fetch_cash_flow(code: str) -> CashFlowStatement` | 股票代码 | 现金流数据 | REQ-002 |
| 获取多年扣非净利 | FinanceFetcher | `fetch_multi_year_deducted_profit(code: str, years: int) -> list[float]` | 股票代码,年数 | 年度扣非净利列表 | REQ-010 |
| 获取市值数据 | MarketFetcher | `fetch_market_data(code: str) -> MarketData` | 股票代码 | 市值数据 | REQ-003 |
| 批量获取市值 | MarketFetcher | `fetch_batch_market_data(codes: list[str]) -> dict[str, MarketData]` | 股票代码列表 | 市值字典 | REQ-003, NFR-001 |
| 获取分红数据 | DividendFetcher | `fetch_dividend_data(code: str) -> DividendData` | 股票代码 | 分红数据 | REQ-004 |

### 业务逻辑层接口

| 接口名称 | 所属模块 | 签名 | 输入 | 输出 | 对应需求 |
|----------|----------|------|------|------|----------|
| 退市风险判断 | DelistingFilter | `is_delisting_risk(stock: StockFullData) -> bool` | 股票完整数据 | 是否有风险 | REQ-013 |
| 批量退市过滤 | DelistingFilter | `filter(stocks: list[StockFullData]) -> list[StockFullData]` | 股票列表 | 过滤后列表 | REQ-013 |
| 资产垫计算 | AssetCushionAnalyzer | `calculate(stock: StockFullData) -> AssetCushionResult` | 股票数据 | 资产垫结果 | REQ-005, REQ-006 |
| 经营安全评估 | OperationSafetyAnalyzer | `evaluate(stock: StockFullData) -> OperationSafetyResult` | 股票数据 | 经营安全结果 | REQ-007, REQ-008 |
| 兑现安全评估 | RedemptionSafetyAnalyzer | `evaluate(stock: StockFullData) -> RedemptionSafetyResult` | 股票数据 | 兑现安全结果 | REQ-009, REQ-010 |
| 综合评分 | Scorer | `score(stock, asset, op, red) -> ScoredResult` | 四项数据 | 评分结果 | REQ-011 |
| 排序 | Scorer | `rank(results: list[ScoredResult]) -> list[ScoredResult]` | 评分列表 | 排序后列表 | REQ-012 |

### 输出层接口

| 接口名称 | 所属模块 | 签名 | 输入 | 输出 | 对应需求 |
|----------|----------|------|------|------|----------|
| 写CSV | CsvWriter | `write(results: list[ScoredResult]) -> str` | 评分结果 | 文件路径 | REQ-015 |
| 打印表格 | TablePrinter | `print(results: list[ScoredResult]) -> None` | 评分结果 | 无 | REQ-015 |

---

# **4. 数据模型**

## **4.1 设计目标**

- 使用 Python `dataclass` 定义所有数据模型，确保类型安全
- 所有金融数值统一使用 `float` 类型，金额单位为**元**（与数据源保持一致）
- 比率类指标统一使用浮点小数（如 0.5 表示 50%）
- 枚举类型使用 Python `enum.Enum` 定义

## **4.2 模型实现**

### 枚举类型

```python
from enum import Enum

class AssetCushionTier(Enum):
    """资产垫等级 (REQ-006)"""
    T0 = "T0"    # 最强资产垫
    T1 = "T1"    # 强资产垫
    T2 = "T2"    # 中等资产垫
    FAIL = "FAIL"  # 不符合

class OperationStatus(Enum):
    """经营安全状态 (REQ-008)"""
    PASS = "PASS"          # 自由现金流>0 且 资本开支率<0.5
    PARTIAL = "PARTIAL"    # 部分满足
    FAIL = "FAIL"          # 不满足

class RedemptionPath(Enum):
    """兑现路径类型 (REQ-009)"""
    DIVIDEND = "分红兑现"           # 持续分红且股息率>2%
    EVENT = "事件兑现"              # 资产处置/股权回购
    EARNINGS_RECOVERY = "盈利恢复"  # 扣非净利为正且递增
    NONE = "无"
```

### 基础数据模型

```python
from dataclasses import dataclass, field

@dataclass
class StockInfo:
    """股票基本信息 (REQ-001)"""
    code: str           # 股票代码，如 "000001"
    name: str           # 股票名称，如 "平安银行"
    exchange: str       # 交易所，如 "SH" / "SZ"

@dataclass
class BalanceSheet:
    """资产负债表 (REQ-002)"""
    cash_and_equivalents: float          # 现金及现金等价物
    total_current_assets: float          # 流动资产合计
    total_assets: float                  # 总资产
    total_current_liabilities: float     # 流动负债合计
    total_liabilities: float             # 总负债
    interest_bearing_debt: float         # 有息负债(短借+长借+应付债券)
    net_assets: float                    # 净资产(所有者权益合计)

@dataclass
class IncomeStatement:
    """利润表 (REQ-002)"""
    revenue: float               # 营业收入
    operating_cost: float        # 营业成本
    net_profit: float            # 净利润
    deducted_net_profit: float   # 扣非净利润

@dataclass
class CashFlowStatement:
    """现金流量表 (REQ-002)"""
    operating_cash_flow: float      # 经营活动现金流净额
    capital_expenditure: float       # 资本开支
    free_cash_flow: float           # 自由现金流(计算得出)

@dataclass
class MarketData:
    """市值数据 (REQ-003)"""
    total_market_cap: float              # 总市值
    circulating_market_cap: float        # 流通市值
    latest_price: float                  # 最新股价

@dataclass
class DividendData:
    """分红数据 (REQ-004)"""
    total_cash_dividend_3y: float    # 近3年累计现金分红金额
    dividend_yield: float            # 股息率
    dividend_years: int              # 近3年分红年数
```

### 聚合数据模型

```python
@dataclass
class StockFullData:
    """股票完整数据（聚合所有数据源）"""
    info: StockInfo
    balance: BalanceSheet
    income: IncomeStatement
    cash_flow: CashFlowStatement
    market: MarketData
    dividend: DividendData
    multi_year_deducted_profits: list[float] = field(default_factory=list)
    is_data_complete: bool = True       # 数据完整性标记 (NFR-005)
    missing_fields: list[str] = field(default_factory=list)  # 缺失字段列表
```

### 业务结果模型

```python
@dataclass
class AssetCushionResult:
    """资产垫评估结果 (REQ-005, REQ-006)"""
    conservative_cash_net: float       # 保守现金净额
    loose_cash_net: float              # 宽松现金净额
    conservative_ratio: float          # 保守资产垫比率
    loose_ratio: float                 # 宽松资产垫比率
    current_asset_net_ratio: float     # 流动资产净值比率
    tier: AssetCushionTier             # 资产垫等级

@dataclass
class OperationSafetyResult:
    """经营安全评估结果 (REQ-007, REQ-008)"""
    free_cash_flow: float              # 自由现金流
    capex_ratio: float                 # 资本开支率
    is_fcf_positive: bool              # FCF>0
    is_capex_ratio_low: bool           # 资本开支率<阈值
    status: OperationStatus            # 经营安全状态

@dataclass
class RedemptionSafetyResult:
    """兑现安全评估结果 (REQ-009, REQ-010)"""
    dividend_path: bool                # 分红兑现路径
    event_path: bool                   # 事件兑现路径
    earnings_path: bool                # 盈利恢复兑现路径
    has_redemption_logic: bool         # 是否满足任一兑现路径
    path_type: str                     # 兑现路径描述

@dataclass
class ScoredResult:
    """综合评分结果 (REQ-011, REQ-012, REQ-014)"""
    stock_code: str                    # 股票代码
    stock_name: str                    # 股票名称
    asset_cushion_tier: AssetCushionTier  # 资产垫等级
    conservative_ratio: float          # 资产垫比率(保守)
    loose_ratio: float                 # 资产垫比率(宽松)
    free_cash_flow: float              # 自由现金流
    capex_ratio: float                 # 资本开支率
    redemption_path_type: str          # 兑现逻辑类型
    asset_cushion_score: float         # 资产垫得分
    operation_safety_score: float      # 经营安全得分
    redemption_safety_score: float     # 兑现安全得分
    total_score: float                 # 综合得分
    rank: int = 0                      # 排名（排序后设置）
```

---

# **5. 错误处理策略**

## **5.1 自定义异常体系**

```python
# common/exceptions.py
class StockSelectionError(Exception):
    """系统基础异常"""

class DataFetchError(StockSelectionError):
    """数据获取异常"""
    stock_code: str
    data_type: str       # 如 "balance_sheet", "market_data"

class DataMissingError(StockSelectionError):
    """数据缺失异常 (NFR-005)"""
    stock_code: str
    missing_fields: list[str]

class DataValidationError(StockSelectionError):
    """数据校验异常（如市值为0导致比率计算异常）"""

class ConfigError(StockSelectionError):
    """配置加载异常"""

class RateLimitError(DataFetchError):
    """API限流异常"""
```

## **5.2 异常处理矩阵**

| 异常场景 | 异常类型 | 处理策略 | 对应需求 |
|----------|----------|----------|----------|
| 网络请求超时 | `DataFetchError` | 重试3次（间隔5秒），仍失败则标记该股数据不完整并跳过 | NFR-002, NFR-005 |
| API返回空数据 | `DataMissingError` | 记录缺失字段，标注"数据不完整"，跳过该股 | NFR-005 |
| 市值为0导致除零 | `DataValidationError` | 跳过该股，记录警告日志 | 防御性编程 |
| API限流(429) | `RateLimitError` | 等待60秒后重试，超过3次放弃 | NFR-002 |
| 配置文件不存在 | `ConfigError` | 使用默认配置，记录警告 | NFR-004 |
| 配置值越界 | `ConfigError` | 校验并回退到默认值 | NFR-004 |
| akshare接口变更 | `DataFetchError` | 尝试备选数据源(tushare/baostock) | CON-002 |
| 单股处理异常 | `StockSelectionError` | 捕获并记录，不影响其他股票处理 | NFR-005 |

## **5.3 重试机制实现**

```python
# common/retry.py
def retry_on_failure(
    max_attempts: int = 3,
    interval_seconds: float = 5.0,
    retryable_exceptions: tuple[type[Exception], ...] = (DataFetchError, RateLimitError),
):
    """
    重试装饰器 (NFR-002)

    用法:
        @retry_on_failure(max_attempts=3, interval_seconds=5)
        def fetch_data(code): ...

    - 每次重试间隔递增（指数退避）：5s, 10s, 20s
    - 记录每次重试日志
    - 超过最大重试次数后抛出最后一次异常
    """
    ...
```

## **5.4 数据缺失处理流程**

```
获取单股数据
    │
    ├─ 成功 → 加入处理列表
    │
    ├─ 部分字段缺失 →
    │   ├─ 关键字段(市值/总负债/现金流)缺失 → 标记"数据不完整"，跳过
    │   └─ 非关键字段缺失 → 用0填充，记录警告，继续处理
    │
    └─ 完全获取失败(重试3次后) → 标记"数据不完整"，跳过
```

---

# **6. 性能优化策略**

## **6.1 批量数据获取 (NFR-001)**

沪深300共300只成分股，逐只请求财务数据耗时长。优化策略：

| 优化措施 | 说明 | 预估效果 |
|----------|------|----------|
| 市值批量获取 | `ak.stock_zh_a_spot_em()` 单次返回全A股行情，内存过滤 | 1次请求替代300次 |
| 数据缓存 | 财务数据缓存4小时（季报更新频率低），行情缓存1小时 | 重复运行秒级完成 |
| 请求间隔控制 | 每次API请求后sleep 0.2秒，避免触发限流 | 稳定性提升 |

## **6.2 性能预估**

| 步骤 | 预估耗时 | 说明 |
|------|----------|------|
| 获取成分股列表 | <2秒 | 单次API调用 |
| 批量获取市值数据 | <5秒 | 单次全市场行情 |
| 逐只获取财务数据(300只) | ~90秒 | 每只0.3秒(含0.2秒间隔) |
| 逐只获取分红数据(300只) | ~90秒 | 每只0.3秒(含0.2秒间隔) |
| 退市过滤+三要义评估 | <5秒 | 纯计算 |
| 排序+输出 | <2秒 | 纯计算+IO |
| **总计** | **~3分钟** | **满足NFR-001的5分钟要求** |

---

# **7. 依赖清单**

## **7.1 requirements.txt**

```
# 数据源
akshare>=1.14.0            # 主数据源：A股财务数据、行情、成分股 (CON-002)

# 数据处理
pandas>=2.0.0              # DataFrame数据处理（akshare返回格式）
pyyaml>=6.0                # YAML配置文件解析 (NFR-004)

# 输出展示
rich>=13.0.0               # 终端美观表格输出 (REQ-015)

# 日志
# logging 为Python标准库，无需额外安装

# 类型支持（Python 3.10+）
# dataclass, enum, typing 为标准库，无需额外安装
```

## **7.2 依赖说明**

| 依赖包 | 版本要求 | 用途 | 是否必需 | 对应约束 |
|--------|----------|------|----------|----------|
| akshare | >=1.14.0 | 主数据源，提供A股全量数据 | 是 | CON-002, CON-004 |
| pandas | >=2.0.0 | akshare返回值处理 | 是 | - |
| pyyaml | >=6.0 | 配置文件加载 | 是 | NFR-004 |
| rich | >=13.0.0 | 终端表格美化 | 是 | REQ-015 |

> **注**: tushare和baostock作为备选数据源，暂不列入主依赖。如需启用备选，需额外安装 `tushare` 和 `baostock`。

---

# **8. 需求追溯矩阵**

| 需求编号 | 需求描述 | 对应模块/接口 | 设计文档章节 |
|----------|----------|---------------|-------------|
| REQ-001 | 获取沪深300成分股 | IndexFetcher.fetch_hs300_constituents() | 1.3.2, 2.2 |
| REQ-002 | 财务数据采集 | FinanceFetcher (三表方法) | 1.3.2, 2.2 |
| REQ-003 | 市值数据获取 | MarketFetcher.fetch_market_data() | 1.3.2, 2.2 |
| REQ-004 | 分红数据获取 | DividendFetcher.fetch_dividend_data() | 1.3.2, 2.2 |
| REQ-005 | 资产垫指标计算 | AssetCushionAnalyzer.calculate() | 1.3.3, 2.2 |
| REQ-006 | 资产垫分级(T0/T1/T2) | AssetCushionAnalyzer._classify_tier() | 1.3.3, 2.2 |
| REQ-007 | 经营安全指标计算 | OperationSafetyAnalyzer.evaluate() | 1.3.3, 2.2 |
| REQ-008 | 经营安全筛选条件 | OperationSafetyAnalyzer.evaluate() | 1.3.3, 2.2 |
| REQ-009 | 兑现安全评估(三条路径) | RedemptionSafetyAnalyzer.evaluate() | 1.3.3, 2.2 |
| REQ-010 | 盈利恢复兑现判断 | RedemptionSafetyAnalyzer._check_earnings_path() | 1.3.3, 2.2 |
| REQ-011 | 综合评分 | Scorer.score() | 1.3.3, 2.2 |
| REQ-012 | 结果排序 | Scorer.rank() | 1.3.3, 2.2 |
| REQ-013 | 退市风险过滤 | DelistingFilter.filter() | 1.3.3, 2.2 |
| REQ-014 | 结果输出内容 | ScoredResult数据模型 | 4.2 |
| REQ-015 | CSV+终端输出 | CsvWriter.write(), TablePrinter.print() | 1.3.4, 2.2 |
| NFR-001 | 5分钟完成 | 批量获取+缓存+性能预估 | 1.3.2, 6 |
| NFR-002 | 重试机制 | retry_on_failure装饰器 | 1.3.2, 5.3 |
| NFR-003 | 运行日志 | LoggerManager | 1.3.4 |
| NFR-004 | 阈值可配置化 | Settings + config.yaml | 1.3.1 |
| NFR-005 | 数据缺失不中断 | DataMissingError + 异常处理 | 5.4 |
| CON-001 | Python 3.10+ | 全部代码 | 全文 |
| CON-002 | akshare优先 | BaseFetcher + 数据源优先级 | 1.3.2, 2.1 |
| CON-003 | Windows+Anaconda | 运行环境 | 7 |
| CON-004 | 不使用付费接口 | akshare选择 | 1.3.2 |
| CON-005 | 仅输出不交易 | main.py无交易逻辑 | 1.3.5 |
