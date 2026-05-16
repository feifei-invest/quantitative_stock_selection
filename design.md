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

---

# **9. 港股通选股扩展技术设计**

## **9.1 扩展架构概述**

### 9.1.1 设计原则

- **适配器模式优先**：通过市场适配器（MarketAdapter）抽象A股/港股数据获取差异，analyzer层零修改复用
- **配置驱动差异**：所有市场差异（字段映射、退市规则、阈值）均通过YAML配置化解，不硬编码
- **最小侵入扩展**：新增港股fetcher子模块，不修改现有A股 fetcher；analyzer层完全复用
- **向后兼容保证**：`market: "A"` 模式下行为与扩展前完全一致

### 9.1.2 扩展后架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                     入口层 (Entry)                                   │
│                main.py (市场模式路由)                                │
├─────────────────────────────────────────────────────────────────────┤
│                   配置层 (Config)                                    │
│          config.yaml + settings.py (+ hk_stock区块)                 │
├─────────────────────────────────────────────────────────────────────┤
│              数据获取层 (DataFetcher) — 适配器模式                    │
│  ┌────────────────────┐  ┌────────────────────┐                     │
│  │   A股 Fetcher      │  │  港股 HK Fetcher   │                     │
│  │ ┌──────────────┐   │  │ ┌──────────────┐   │                     │
│  │ │IndexFetcher  │   │  │ │HKIndexFetcher│   │                     │
│  │ │FinanceFetcher│   │  │ │HKFinanceFetr│   │ ← 字段映射适配器     │
│  │ │MarketFetcher │   │  │ │HKMarketFetcr│   │                     │
│  │ │DividendFetcr │   │  │ │HKDividendFtr│   │ ← 仙/港元转换       │
│  │ └──────────────┘   │  │ └──────────────┘   │                     │
│  └────────────────────┘  └────────────────────┘                     │
│           │                        │                                 │
│           └────────┬───────────────┘                                │
│                    ▼ 统一输出: StockFullData                         │
├─────────────────────────────────────────────────────────────────────┤
│            业务逻辑层 (Analyzer) — 完全复用，零修改                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │退市风险过滤│ │资产垫评估 │ │经营安全评估│ │兑现安全评估│              │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │
│  ┌──────────┐ ┌──────────────────┐                                 │
│  │综合评分  │ │HKDelistingFilter │ ← 仅退市过滤替换                 │
│  └──────────┘ └──────────────────┘                                 │
├─────────────────────────────────────────────────────────────────────┤
│                 输出层 (Output)                                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                     │
│  │ CSV 输出器  │ │表格输出器  │ │ 日志记录器  │                     │
│  └────────────┘ └────────────┘ └────────────┘                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.1.3 扩展后目录结构（增量部分）

```
quantitative_stock_selection/
├── fetcher/                         # 数据获取层（扩展）
│   ├── hk/                          # ★ 港股数据获取子模块
│   │   ├── __init__.py
│   │   ├── hk_index_fetcher.py      # ★ 港股通成分股获取 (REQ-HK-001)
│   │   ├── hk_finance_fetcher.py    # ★ 港股财务数据获取+字段映射 (REQ-HK-004~008)
│   │   ├── hk_market_fetcher.py     # ★ 港股市值数据获取 (REQ-HK-009)
│   │   ├── hk_dividend_fetcher.py   # ★ 港股分红数据获取 (REQ-HK-011)
│   │   └── field_mapper.py          # ★ IFRS/HKFRS字段映射器 (NFR-HK-002)
│   ├── ... (现有A股fetcher不变)
│
├── analyzer/                        # 业务逻辑层（仅新增港股退市过滤）
│   ├── hk_delisting_filter.py       # ★ 港股退市风险过滤 (REQ-HK-016~019)
│   ├── ... (现有analyzer完全复用，不修改)
│
├── common/                          # 公共层（扩展模型）
│   ├── models.py                    # 扩展: StockInfo增加market字段
│   ├── ... (其余不变)
│
├── config/                          # 配置管理（扩展）
│   ├── settings.py                  # 扩展: 增加HKStockConfig等
│   ├── default_config.yaml          # 扩展: 增加hk_stock配置区块
│   ├── hk_field_mapping.yaml        # ★ 港股财务字段映射配置 (NFR-HK-002, NFR-HK-003)
│
├── main.py                          # 扩展: 市场模式路由
```

> ★ 标记为新增文件/模块，现有A股代码零修改

---

## **9.2 模块扩展详细设计**

### 9.2.1 公共数据模型扩展

#### StockInfo 扩展

```python
# common/models.py — 扩展StockInfo
@dataclass
class StockInfo:
    code: str = ""           # 股票代码（A股6位/港股5位）
    name: str = ""           # 股票名称
    exchange: str = ""       # 交易所: "SH"/"SZ"/"HK"
    market: str = "A"        # ★ 市场标识: "A" / "HK"
```

#### ScoredResult 扩展

```python
# common/models.py — 扩展ScoredResult
@dataclass
class ScoredResult:
    stock_code: str = ""
    stock_name: str = ""
    market: str = "A"                           # ★ 市场标识
    currency: str = "CNY"                       # ★ 货币单位: "CNY"/"HKD"
    deducted_net_profit_is_estimated: bool = False  # ★ 扣非净利润是否为估算值
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
```

> **设计要点**：通过新增可选字段（带默认值）扩展模型，现有A股代码的ScoredResult构造无需修改，默认值 `"A"` / `"CNY"` / `False` 保证向后兼容。

---

### 9.2.2 港股通成分股获取 (REQ-HK-001~003)

#### HKIndexFetcher

```python
# fetcher/hk/hk_index_fetcher.py
class HKIndexFetcher(BaseFetcher):
    """
    港股通成分股获取

    数据源: akshare stock_hk_ggt_components_em 接口
    合并沪港通+深港通标的并去重

    对应需求: REQ-HK-001, REQ-HK-002, REQ-HK-003
    """

    def __init__(self, settings: Settings, cache: DataCache):
        super().__init__(settings)
        self.cache = cache

    def fetch(self) -> list[StockInfo]:
        """
        获取港股通全部标的股票

        Returns:
            list[StockInfo]: 港股通成分股列表
                - code: 5位港股代码（如"00700"）
                - name: 股票名称
                - exchange: "HK"
                - market: "HK"

        流程:
        1. 获取沪港通标的 (include_sse=true时)
        2. 获取深港通标的 (include_szse=true时)
        3. 合并去重（以股票代码为唯一键）
        4. 记录沪港通/深港通标的数量日志

        对应需求: REQ-HK-001, REQ-HK-002
        """
        ...

    def _fetch_sse_constituents(self) -> list[StockInfo]:
        """获取沪港通标的 (akshare: stock_hk_ggt_components_em(indicator="沪港通"))"""
        ...

    def _fetch_szse_constituents(self) -> list[StockInfo]:
        """获取深港通标的 (akshare: stock_hk_ggt_components_em(indicator="深港通"))"""
        ...

    def _merge_and_deduplicate(
        self, sse_list: list[StockInfo], szse_list: list[StockInfo]
    ) -> list[StockInfo]:
        """合并去重，以5位港股代码为唯一键"""
        ...
```

#### akshare接口映射

| 数据项 | akshare接口 | 参数 | 返回字段映射 | 对应需求 |
|--------|-------------|------|-------------|----------|
| 沪港通标的 | `ak.stock_hk_ggt_components_em(indicator="沪港通")` | indicator | 港股代码→code, 港股名称→name | REQ-HK-001 |
| 深港通标的 | `ak.stock_hk_ggt_components_em(indicator="深港通")` | indicator | 同上 | REQ-HK-001 |

---

### 9.2.3 港股财务数据获取与字段映射 (REQ-HK-004~008)

#### FieldMapper — IFRS/HKFRS字段映射器

```python
# fetcher/hk/field_mapper.py
class FieldMapper:
    """
    港股财务字段映射器

    将IFRS/HKFRS财报字段名映射为系统标准字段名。
    映射关系从hk_field_mapping.yaml加载，支持配置化修改。

    对应需求: NFR-HK-002, NFR-HK-003
    """

    def __init__(self, mapping_config: dict):
        """
        Args:
            mapping_config: 从hk_field_mapping.yaml加载的映射配置
        """
        self._balance_mapping = mapping_config.get("balance_sheet", {})
        self._income_mapping = mapping_config.get("income_statement", {})
        self._cashflow_mapping = mapping_config.get("cash_flow", {})
        self._interest_debt_items = mapping_config.get(
            "interest_bearing_debt_items", []
        )

    def map_balance_sheet(self, raw_row: pd.Series) -> dict:
        """
        映射港股资产负债表字段

        特殊处理:
        - 有息负债: 按配置的interest_bearing_debt_items逐项累加
        - 应付债券缺失时计为0 (REQ-HK-005)
        - 净资产: 优先"归属母公司股东权益"

        Returns:
            dict: 符合BalanceSheet字段名的字典

        对应需求: REQ-HK-004, REQ-HK-005
        """
        ...

    def map_income_statement(self, raw_row: pd.Series) -> dict:
        """
        映射港股利润表字段

        特殊处理:
        - 扣非净利润缺失时使用净利润替代 (REQ-HK-007)
        - 返回值增加 deducted_net_profit_is_estimated 标记

        对应需求: REQ-HK-006, REQ-HK-007
        """
        ...

    def map_cash_flow(self, raw_row: pd.Series) -> dict:
        """
        映射港股现金流量表字段

        特殊处理:
        - capital_expenditure: IFRS常用"Purchase of PPE"
        - free_cash_flow: 计算得出 = OCF - CAPEX

        对应需求: REQ-HK-008
        """
        ...

    def _calc_interest_bearing_debt(self, raw_row: pd.Series) -> float:
        """
        按配置的有息负债科目列表逐项累加

        港股有息负债 = 短期银行借款 + 长期银行借款 + 应付债券 + 融资租赁负债
        缺失科目计为0

        对应需求: REQ-HK-005
        """
        ...
```

#### hk_field_mapping.yaml — 字段映射配置

```yaml
# config/hk_field_mapping.yaml
# 港股IFRS/HKFRS财报字段 → 系统标准字段映射
# 修改此文件即可适配数据源字段变更，无需修改代码 (NFR-HK-003)

balance_sheet:
  cash_and_equivalents:
    - "Cash and cash equivalents"
    - "现金及现金等价物"
    - "货币资金"
  total_current_assets:
    - "Total current assets"
    - "流动资产合计"
  total_assets:
    - "Total assets"
    - "资产总计"
  total_current_liabilities:
    - "Total current liabilities"
    - "流动负债合计"
  total_liabilities:
    - "Total liabilities"
    - "负债合计"
  net_assets:
    - "Equity attributable to owners of the parent"
    - "归属母公司股东权益"
    - "归属于母公司股东权益合计"

# 有息负债组成科目（按港交所IFRS定义）
interest_bearing_debt_items:
  - "Short-term bank borrowings"
  - "短期银行借款"
  - "Long-term bank borrowings"
  - "长期银行借款"
  - "Bonds payable"
  - "应付债券"
  - "Lease liabilities"
  - "融资租赁负债"

income_statement:
  revenue:
    - "Revenue"
    - "营业收入"
  operating_cost:
    - "Cost of sales"
    - "营业成本"
  net_profit:
    - "Profit for the year"
    - "净利润"
  deducted_net_profit:
    - "Profit excluding non-recurring items"
    - "扣除非经常性损益后的净利润"

cash_flow:
  operating_cash_flow:
    - "Net cash from operating activities"
    - "经营活动产生的现金流量净额"
  capital_expenditure:
    - "Purchase of property, plant and equipment"
    - "购建固定资产、无形资产和其他长期资产支付的现金"
    - "Purchase of PPE"
```

> **设计要点**：每个标准字段映射为一组候选字段名（按优先级排列），FieldMapper按顺序匹配原始数据中存在的字段。新增映射关系仅需修改YAML文件，无需修改代码（NFR-HK-002, NFR-HK-003）。

#### HKFinanceFetcher

```python
# fetcher/hk/hk_finance_fetcher.py
class HKFinanceFetcher(BaseFetcher):
    """
    港股财务数据获取

    与A股FinanceFetcher的核心差异:
    1. 数据源接口不同（港股财报接口）
    2. 字段名不同（IFRS/HKFRS vs 中国会计准则）
    3. 有息负债计算逻辑不同（含融资租赁负债）
    4. 扣非净利润可能缺失（用净利润替代）

    输出统一为BalanceSheet/IncomeStatement/CashFlowStatement，
    analyzer层无需修改。

    对应需求: REQ-HK-004~008
    """

    def __init__(self, settings: Settings, cache: DataCache, field_mapper: FieldMapper):
        super().__init__(settings)
        self.cache = cache
        self.field_mapper = field_mapper

    def fetch_balance_sheet(self, stock_code: str) -> BalanceSheet:
        """
        获取港股资产负债表

        数据源: akshare 港股财务报表接口
        字段映射: 通过FieldMapper.map_balance_sheet()转换
        有息负债: 通过FieldMapper._calc_interest_bearing_debt()按配置科目累加

        对应需求: REQ-HK-004, REQ-HK-005
        """
        ...

    def fetch_income_statement(self, stock_code: str) -> tuple[IncomeStatement, bool]:
        """
        获取港股利润表

        Returns:
            tuple[IncomeStatement, bool]: (利润表数据, 扣非净利润是否为估算值)

        特殊处理:
        - 港股可能不披露扣非净利润 → 使用净利润替代，标记为估算 (REQ-HK-007)

        对应需求: REQ-HK-006, REQ-HK-007
        """
        ...

    def fetch_cash_flow(self, stock_code: str) -> CashFlowStatement:
        """
        获取港股现金流量表

        对应需求: REQ-HK-008
        """
        ...

    def fetch_multi_year_deducted_profit(
        self, stock_code: str, years: int = 3
    ) -> list[float]:
        """
        获取港股近N年扣非净利润

        港股扣非净利润可能缺失 → 使用净利润替代

        对应需求: REQ-HK-007
        """
        ...
```

#### akshare港股财报接口映射

| 数据项 | akshare接口 | 参数 | 对应需求 |
|--------|-------------|------|----------|
| 港股资产负债表 | `ak.stock_hk_financial_report_em(symbol="00700", indicator="资产负债表")` | symbol=5位港股代码 | REQ-HK-004 |
| 港股利润表 | `ak.stock_hk_financial_report_em(symbol="00700", indicator="利润表")` | 同上 | REQ-HK-006 |
| 港股现金流量表 | `ak.stock_hk_financial_report_em(symbol="00700", indicator="现金流量表")` | 同上 | REQ-HK-008 |

---

### 9.2.4 港股市值数据获取 (REQ-HK-009, REQ-HK-010)

#### HKMarketFetcher

```python
# fetcher/hk/hk_market_fetcher.py
class HKMarketFetcher(BaseFetcher):
    """
    港股市值数据获取

    与A股MarketFetcher的差异:
    1. 数据源: akshare港股实时行情 (stock_hk_spot_em)
    2. 市值单位: 港币（HKD），而非人民币
    3. 腾讯行情港股接口前缀为"hk"（如 hk00700）

    对应需求: REQ-HK-009, REQ-HK-010
    """

    def __init__(self, settings: Settings, cache: DataCache):
        super().__init__(settings)
        self.cache = cache

    def fetch_batch_market_data(self, stock_codes: list[str]) -> dict[str, MarketData]:
        """
        批量获取港股市值数据

        优先级:
        1. 腾讯行情港股接口（速度快，批量）
        2. akshare stock_hk_spot_em（备选）

        市值数据缺失的股票跳过，不中断流程 (REQ-HK-010)

        对应需求: REQ-HK-009
        """
        ...

    def _fetch_via_tencent_hk(self, stock_codes: list[str]) -> dict:
        """
        腾讯行情港股接口

        港股代码前缀: hk（如 hk00700）
        URL: http://qt.gtimg.cn/q=hk00700,hk00941,...

        返回字段解析同A股腾讯行情，市值单位为港币
        """
        ...

    def _fetch_via_akshare_hk(self) -> dict:
        """
        akshare港股实时行情

        接口: ak.stock_hk_spot_em()
        返回全港股行情，内存过滤港股通标的
        """
        ...
```

#### 腾讯行情港股接口说明

```
A股格式: sh600000, sz000001 → http://qt.gtimg.cn/q=sh600000
港股格式: hk00700, hk00941 → http://qt.gtimg.cn/q=hk00700

返回数据字段位置与A股基本一致:
- fields[3]: 最新价（港币）
- fields[44]: 流通市值（亿港元）
- fields[45]: 总市值（亿港元）
```

---

### 9.2.5 港股分红数据获取 (REQ-HK-011~013)

#### HKDividendFetcher

```python
# fetcher/hk/hk_dividend_fetcher.py
class HKDividendFetcher(BaseFetcher):
    """
    港股分红数据获取

    与A股DividendFetcher的差异:
    1. 数据源: akshare港股分红接口
    2. 单位转换: 港仙(cent) → 港元(HKD)，除以100 (REQ-HK-012)
    3. A股"每10股派X元" → 港股"每股派X仙/元"

    对应需求: REQ-HK-011, REQ-HK-012, REQ-HK-013
    """

    def __init__(self, settings: Settings, cache: DataCache):
        super().__init__(settings)
        self.cache = cache

    def fetch_dividend_data(
        self, stock_code: str, latest_price: float = 0.0
    ) -> DividendData:
        """
        获取港股近3年分红数据

        单位转换逻辑:
        - 若分红数据单位为"仙(cent)" → 除以100转为港元
        - 若分红数据单位为"元(HKD)" → 直接使用
        - 通过字段名或单位标识自动判断

        分红获取失败 → 返回默认值(0)，不中断流程 (REQ-HK-013)

        对应需求: REQ-HK-011, REQ-HK-012
        """
        ...

    def _convert_cent_to_hkd(self, value: float) -> float:
        """
        港仙转港元: value / 100

        对应需求: REQ-HK-012
        """
        return value / 100.0
```

#### akshare港股分红接口映射

| 数据项 | akshare接口 | 参数 | 单位处理 | 对应需求 |
|--------|-------------|------|----------|----------|
| 港股分红明细 | `ak.stock_hk_dividend_detail(symbol="00700")` | symbol=5位港股代码 | 仙→港元: /100 | REQ-HK-011 |

---

### 9.2.6 港股退市风险过滤 (REQ-HK-016~019)

#### HKDelistingFilter

```python
# analyzer/hk_delisting_filter.py
class HKDelistingFilter:
    """
    港股退市风险过滤

    与A股DelistingFilter的核心差异:
    1. 不使用ST标记制度（港交所无ST机制）
    2. 使用港交所退市规则:
       - 连续停牌超过3个月 → 剔除
       - 净资产为负 → 剔除
       - 非标审计意见 → 剔除
       - 市值低于5,000万港元 → 剔除
       - 退市整理期 → 剔除
    3. 无法判断时保留股票，记录警告 (REQ-HK-019)

    对应需求: REQ-HK-016~019
    """

    def __init__(self, config: HKDelistingConfig):
        self.config = config

    def is_delisting_risk(self, stock: StockFullData) -> bool:
        """
        判断港股是否存在退市风险

        过滤顺序:
        1. 停牌时长过滤 (REQ-HK-017)
        2. 净资产为负过滤 (REQ-HK-017)
        3. 审计意见过滤 (REQ-HK-017)
        4. 最低市值过滤 (REQ-HK-017)
        5. 退市整理期过滤 (REQ-HK-018)

        对应需求: REQ-HK-016
        """
        ...

    def filter(self, stocks: list[StockFullData]) -> list[StockFullData]:
        """批量过滤"""
        ...

    def _check_suspend_duration(self, stock: StockFullData) -> bool:
        """
        连续停牌超过max_suspend_months个月 → 剔除

        数据来源: 港股行情中的停牌标记/停牌日期
        """
        ...

    def _check_negative_net_assets(self, stock: StockFullData) -> bool:
        """净资产(归属母公司股东权益) < 0 → 剔除"""
        return stock.balance.net_assets < 0

    def _check_audit_opinion(self, stock: StockFullData) -> bool:
        """
        审计意见为"无法表示意见"或"否定意见" → 剔除

        缺少审计意见信息 → 保留，记录警告 (REQ-HK-019)
        """
        ...

    def _check_min_market_cap(self, stock: StockFullData) -> bool:
        """
        总市值 < min_market_cap_hkd → 剔除

        默认最低市值: 50,000,000港元 (5,000万)
        """
        return stock.market.total_market_cap < self.config.min_market_cap_hkd

    def _check_delisting_period(self, stock: StockFullData) -> bool:
        """
        处于退市整理期 → 剔除 (REQ-HK-018)

        通过股票名称中的"退市"标记判断
        """
        ...
```

---

### 9.2.7 analyzer层复用方案 (REQ-HK-020, REQ-HK-021, NFR-HK-004)

#### 复用策略

| analyzer模块 | 复用方式 | 差异处理 | 对应需求 |
|-------------|---------|---------|---------|
| `AssetCushionAnalyzer` | **完全复用**，零修改 | 港股阈值通过`hk_stock.asset_cushion`配置独立覆盖 | REQ-HK-020, REQ-HK-021 |
| `OperationSafetyAnalyzer` | **完全复用**，零修改 | 无差异，评估标准不变 | REQ-HK-020 |
| `RedemptionSafetyAnalyzer` | **完全复用**，零修改 | 无差异，评估标准不变 | REQ-HK-020 |
| `Scorer` | **完全复用**，零修改 | 港股评分权重通过`hk_stock.scoring`配置独立覆盖 | REQ-HK-020, REQ-HK-021 |
| `DelistingFilter` | **不复用**，新建`HKDelistingFilter` | 港交所退市规则与A股完全不同 | REQ-HK-016 |

#### 关键设计：配置覆盖机制

```python
# 港股analyzer初始化时使用港股专用配置
def _get_hk_asset_cushion_config(settings: Settings) -> AssetCushionConfig:
    """
    获取港股资产垫配置

    优先使用hk_stock.asset_cushion配置，
    未定义时回退到A股默认配置 (REQ-HK-027)
    """
    if settings.hk_stock and settings.hk_stock.asset_cushion:
        return settings.hk_stock.asset_cushion
    return settings.asset_cushion  # 回退到A股配置
```

> **设计要点**：analyzer层完全复用的前提是港股fetcher输出与A股相同的数据模型（`StockFullData`）。所有市场差异在fetcher层通过字段映射和单位转换"消化"，analyzer层只看到统一模型。

---

### 9.2.8 配置扩展设计 (REQ-HK-025~027)

#### settings.py 新增配置类

```python
# config/settings.py — 新增

@dataclass
class HKConstituentsConfig:
    include_sse: bool = True          # 包含沪港通标的
    include_szse: bool = True         # 包含深港通标的

@dataclass
class HKCurrencyConfig:
    unit: str = "HKD"                 # 货币单位
    convert_to_cny: bool = False      # 是否换算为人民币
    fixed_hkd_cny_rate: float = 0.0  # 固定汇率（0表示实时获取）

@dataclass
class HKDelistingConfig:
    max_suspend_months: int = 3       # 最大停牌月数
    min_market_cap_hkd: float = 50000000.0  # 最低市值（港元）
    filter_audit_opinion: bool = True  # 是否过滤非标审计意见

@dataclass
class HKDataSourceConfig:
    primary: str = "akshare"          # 港股数据源
    fallback: str = "eastmoney"       # 备选数据源

@dataclass
class HKStockConfig:
    data_source: HKDataSourceConfig = field(default_factory=HKDataSourceConfig)
    constituents: HKConstituentsConfig = field(default_factory=HKConstituentsConfig)
    currency: HKCurrencyConfig = field(default_factory=HKCurrencyConfig)
    delisting: HKDelistingConfig = field(default_factory=HKDelistingConfig)
    # 港股专用analyzer配置（可选覆盖A股默认）
    asset_cushion: AssetCushionConfig = field(default_factory=AssetCushionConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)

# Settings 扩展
@dataclass
class Settings:
    # ... 现有字段不变 ...
    market: str = "ALL"                        # ★ 市场模式: "A" / "HK" / "ALL"
    hk_stock: HKStockConfig = field(default_factory=HKStockConfig)  # ★ 港股配置
```

#### config.yaml 新增港股配置区块

```yaml
# config.yaml — 新增港股配置区块

# 市场模式 (REQ-HK-025)
market: "ALL"  # "A": 仅A股 | "HK": 仅港股 | "ALL": A股+港股

# 港股通专用配置 (REQ-HK-026)
hk_stock:
  data_source:
    primary: "akshare"
    fallback: "eastmoney"
  constituents:
    include_sse: true              # 包含沪港通标的
    include_szse: true             # 包含深港通标的
  currency:
    unit: "HKD"                    # 货币单位
    convert_to_cny: false          # 是否换算为人民币 (REQ-HK-015)
    fixed_hkd_cny_rate: 0          # 固定汇率（0=实时获取）
  delisting:
    max_suspend_months: 3          # 最大停牌月数 (REQ-HK-017)
    min_market_cap_hkd: 50000000   # 最低市值5,000万港元 (REQ-HK-017)
    filter_audit_opinion: true     # 过滤非标审计意见 (REQ-HK-017)
  # 港股专用资产垫阈值（可选，未定义时使用A股默认值）(REQ-HK-021)
  asset_cushion:
    t0:
      min_conservative_ratio: 0.7  # 港股T0保守比率（比A股0.8更宽松）
      min_loose_ratio: 1.5
    t1:
      min_loose_ratio: 1.0
      require_positive_conservative: true
    t2:
      require_positive_loose: true
      min_current_asset_net_ratio: 0.5
  # 港股专用评分权重（可选）(REQ-HK-021)
  scoring:
    weights:
      asset_cushion: 0.4
      operation_safety: 0.3
      redemption_safety: 0.3
    scores:
      t0: 100
      t1: 70
      t2: 40
      fail: 0
      operation_pass: 100
      operation_partial: 50
      operation_fail: 0
      redemption_pass: 100
      redemption_fail: 0
```

---

### 9.2.9 主程序入口扩展 (REQ-HK-028~031)

#### main.py 市场模式路由

```python
# main.py — 扩展

def main():
    settings = Settings.load("config.yaml")
    logger = LoggerManager.setup(...)

    market = settings.market  # "A" / "HK" / "ALL"

    if market in ("A", "ALL"):
        logger.info("=" * 60)
        logger.info(f"{'A股模式' if market == 'A' else '全市场模式'} — A股选股启动")
        logger.info("=" * 60)
        run_a_stock_selection(settings, logger)

    if market in ("HK", "ALL"):
        logger.info("=" * 60)
        logger.info(f"{'港股通模式' if market == 'HK' else '全市场模式'} — 港股选股启动")
        logger.info("=" * 60)
        run_hk_stock_selection(settings, logger)


def run_a_stock_selection(settings: Settings, logger: logging.Logger) -> list[ScoredResult]:
    """
    A股选股流程（与原main()逻辑完全一致）

    向后兼容: market="A" 时行为与扩展前完全一致 (REQ-HK-030)
    """
    # ... 原有A股流程代码，不修改 ...


def run_hk_stock_selection(settings: Settings, logger: logging.Logger) -> list[ScoredResult]:
    """
    港股通选股流程 (REQ-HK-028)

    完整流程:
    1. 港股通成分股获取 (HKIndexFetcher)
    2. 港股市值数据批量获取 (HKMarketFetcher)
    3. 港股财务数据逐只获取 (HKFinanceFetcher + FieldMapper)
    4. 港股分红数据逐只获取 (HKDividendFetcher, 仙→港元转换)
    5. 港股退市风险过滤 (HKDelistingFilter, 港交所规则)
    6. 核心筛选与评分（复用A股analyzer: AssetCushion/OperationSafety/RedemptionSafety/Scorer）
    7. 港股结果输出（独立CSV, 文件名含hk标识）
    """
    cache = DataCache(...)

    # Step 1: 港股通成分股
    hk_index_fetcher = HKIndexFetcher(settings, cache)
    constituents = hk_index_fetcher.fetch()

    # Step 2: 港股市值数据
    hk_market_fetcher = HKMarketFetcher(settings, cache)
    market_data_map = hk_market_fetcher.fetch_batch_market_data(codes)

    # Step 3: 港股财务数据（含字段映射）
    field_mapper = FieldMapper(HKFieldMappingLoader.load())
    hk_finance_fetcher = HKFinanceFetcher(settings, cache, field_mapper)
    # ... 逐只获取三表+多年扣非净利 ...

    # Step 4: 港股分红数据
    hk_dividend_fetcher = HKDividendFetcher(settings, cache)
    # ... 逐只获取分红 ...

    # Step 5: 港股退市过滤（港交所规则）
    hk_delisting_filter = HKDelistingFilter(settings.hk_stock.delisting)
    filtered = hk_delisting_filter.filter(full_data_list)

    # Step 6: 核心筛选（复用A股analyzer，使用港股专用配置）
    hk_ac_config = _get_hk_asset_cushion_config(settings)
    asset_analyzer = AssetCushionAnalyzer(hk_ac_config)
    operation_analyzer = OperationSafetyAnalyzer(settings.operation_safety)
    redemption_analyzer = RedemptionSafetyAnalyzer(settings.redemption_safety)
    hk_scoring_config = _get_hk_scoring_config(settings)
    scorer = Scorer(hk_scoring_config)
    # ... 逐只评估+评分 ...

    # Step 7: 港股结果输出
    # CSV文件名: hk_stock_selection_result_YYYYMMDD_HHMMSS.csv
    csv_writer = CsvWriter(csv_dir=settings.output.csv_dir, encoding=settings.output.csv_encoding)
    csv_path = csv_writer.write_hk(scored_results)  # 港股专用输出方法
    table_printer = TablePrinter(...)
    table_printer.print(scored_results)

    return scored_results
```

---

### 9.2.10 输出层扩展 (REQ-HK-022~024)

#### CsvWriter 扩展

```python
# output/csv_writer.py — 扩展

def format_scored_result(r: ScoredResult) -> dict:
    """统一格式化，支持A股和港股"""
    result = {
        "排名": r.rank,
        "股票代码": r.stock_code,
        "股票名称": r.stock_name,
        "市场": r.market,                           # ★ 新增
        "货币": r.currency,                         # ★ 新增
        "资产垫等级": r.asset_cushion_tier,
        "保守资产垫比率": f"{r.conservative_ratio:.4f}",
        "宽松资产垫比率": f"{r.loose_ratio:.4f}",
        f"自由现金流({r.currency})": f"{r.free_cash_flow:,.0f}",  # ★ 动态货币单位
        "资本开支率": f"{r.capex_ratio:.4f}" if r.capex_ratio != float("inf") else "N/A",
        "兑现路径": r.redemption_path_type,
        "资产垫得分": f"{r.asset_cushion_score:.0f}",
        "经营安全得分": f"{r.operation_safety_score:.0f}",
        "兑现安全得分": f"{r.redemption_safety_score:.0f}",
        "综合评分": f"{r.total_score:.2f}",
    }
    # 港股附加字段
    if r.market == "HK":
        result["扣非净利润估算"] = "是" if r.deducted_net_profit_is_estimated else "否"
    return result


class CsvWriter:
    # ... 现有方法不变 ...

    def write_hk(self, results: list[ScoredResult]) -> str:
        """
        写入港股选股结果CSV

        文件名: hk_stock_selection_YYYYMMDD_HHMMSS.csv
        与A股结果独立，不合并 (REQ-HK-023, REQ-HK-024)

        对应需求: REQ-HK-022, REQ-HK-023
        """
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.csv_dir, f"hk_stock_selection_{date_str}.csv")
        # ... 写入逻辑与write()相同，仅文件名不同 ...
```

---

### 9.2.11 货币与汇率处理 (REQ-HK-014, REQ-HK-015)

```python
# fetcher/hk/currency_converter.py (可选新增)
class CurrencyConverter:
    """
    港币/人民币汇率转换

    默认关闭汇率换算，各市场独立计价 (REQ-HK-014)
    仅当配置convert_to_cny=true时启用 (REQ-HK-015)
    """

    def __init__(self, config: HKCurrencyConfig):
        self.config = config
        self._rate: float = 0.0

    def get_hkd_cny_rate(self) -> float:
        """
        获取HKD/CNY汇率

        优先级:
        1. 配置文件固定汇率 (fixed_hkd_cny_rate > 0)
        2. akshare实时汇率接口
        """
        if self.config.fixed_hkd_cny_rate > 0:
            return self.config.fixed_hkd_cny_rate
        # akshare汇率接口获取实时汇率
        ...

    def convert_hkd_to_cny(self, amount_hkd: float) -> float:
        """港元 → 人民币（仅当convert_to_cny=True时调用）"""
        if not self.config.convert_to_cny:
            return amount_hkd
        return amount_hkd * self.get_hkd_cny_rate()
```

---

## **9.3 港股通接口清单**

### 数据获取层新增接口

| 接口名称 | 所属模块 | 签名 | 输入 | 输出 | 对应需求 |
|----------|----------|------|------|------|----------|
| 获取港股通成分股 | HKIndexFetcher | `fetch() -> list[StockInfo]` | 无 | 港股通成分股列表 | REQ-HK-001 |
| 港股资产负债表 | HKFinanceFetcher | `fetch_balance_sheet(code) -> BalanceSheet` | 5位港股代码 | 资产负债表 | REQ-HK-004 |
| 港股利润表 | HKFinanceFetcher | `fetch_income_statement(code) -> tuple[IncomeStatement, bool]` | 5位港股代码 | (利润表, 是否估算) | REQ-HK-006 |
| 港股现金流量表 | HKFinanceFetcher | `fetch_cash_flow(code) -> CashFlowStatement` | 5位港股代码 | 现金流数据 | REQ-HK-008 |
| 港股多年净利 | HKFinanceFetcher | `fetch_multi_year_deducted_profit(code, years) -> list[float]` | 代码,年数 | 年度净利列表 | REQ-HK-007 |
| 港股批量市值 | HKMarketFetcher | `fetch_batch_market_data(codes) -> dict[str, MarketData]` | 代码列表 | 市值字典 | REQ-HK-009 |
| 港股分红数据 | HKDividendFetcher | `fetch_dividend_data(code, price) -> DividendData` | 代码,股价 | 分红数据 | REQ-HK-011 |
| 字段映射-资产负债表 | FieldMapper | `map_balance_sheet(row) -> dict` | 原始行数据 | 标准字段字典 | NFR-HK-002 |
| 字段映射-利润表 | FieldMapper | `map_income_statement(row) -> dict` | 原始行数据 | 标准字段字典 | NFR-HK-002 |
| 字段映射-现金流 | FieldMapper | `map_cash_flow(row) -> dict` | 原始行数据 | 标准字段字典 | NFR-HK-002 |

### 业务逻辑层新增接口

| 接口名称 | 所属模块 | 签名 | 输入 | 输出 | 对应需求 |
|----------|----------|------|------|------|----------|
| 港股退市风险判断 | HKDelistingFilter | `is_delisting_risk(stock) -> bool` | 股票完整数据 | 是否有风险 | REQ-HK-016 |
| 港股批量退市过滤 | HKDelistingFilter | `filter(stocks) -> list[StockFullData]` | 股票列表 | 过滤后列表 | REQ-HK-016 |
| 港股CSV输出 | CsvWriter | `write_hk(results) -> str` | 评分结果 | 文件路径 | REQ-HK-022 |

---

## **9.4 港股通数据模型扩展**

### 新增枚举

无新增枚举。A股/港股复用相同的 `AssetCushionTier`、`OperationStatus`、`RedemptionPath`。

### 模型扩展汇总

| 模型 | 扩展字段 | 类型 | 默认值 | 用途 |
|------|---------|------|--------|------|
| `StockInfo` | `market` | `str` | `"A"` | 市场标识 |
| `ScoredResult` | `market` | `str` | `"A"` | 市场标识 |
| `ScoredResult` | `currency` | `str` | `"CNY"` | 货币单位 |
| `ScoredResult` | `deducted_net_profit_is_estimated` | `bool` | `False` | 扣非净利润是否为估算值 |

> **兼容性保证**：所有扩展字段均有默认值，现有A股代码中构造 `StockInfo` 和 `ScoredResult` 时无需传入新字段，自动使用默认值 `"A"` / `"CNY"` / `False`。

---

## **9.5 港股通错误处理策略**

### 港股专用异常场景

| 异常场景 | 异常类型 | 处理策略 | 对应需求 |
|----------|----------|----------|----------|
| 港股通成分股获取失败 | `DataFetchError` | 记录错误日志，终止港股选股流程 | REQ-HK-003 |
| 港股市值数据缺失 | — | 标注"市值数据缺失"，跳过该股 | REQ-HK-010 |
| 港股分红数据获取失败 | — | 默认值(0)，记录警告，不中断 | REQ-HK-013 |
| 港股扣非净利润缺失 | — | 使用净利润替代，标记为估算 | REQ-HK-007 |
| 港股退市风险无法判断 | — | 保留股票，记录警告 | REQ-HK-019 |
| 港股财报字段名变更 | — | 修改hk_field_mapping.yaml，无需改代码 | NFR-HK-003 |
| 汇率获取失败 | `DataFetchError` | 使用固定汇率或跳过汇率换算 | REQ-HK-015 |

---

## **9.6 港股通性能预估**

| 步骤 | 预估耗时 | 说明 |
|------|----------|------|
| 获取港股通成分股 | <3秒 | 2次API调用（沪港通+深港通） |
| 批量获取港股市值数据 | <10秒 | 腾讯行情港股接口批量 |
| 逐只获取港股财务数据(~500只) | ~200秒 | 每只0.4秒（港股接口较慢） |
| 逐只获取港股分红数据(~500只) | ~150秒 | 每只0.3秒 |
| 港股退市过滤+三要义评估 | <5秒 | 纯计算 |
| 排序+输出 | <2秒 | 纯计算+IO |
| **总计** | **~6分钟** | **满足NFR-HK-001的8分钟要求** |

> 港股通标的约500只，多于沪深300的300只，且港股数据源响应较慢，适当放宽至8分钟（NFR-HK-001）。

---

## **9.7 港股通依赖清单**

### 新增依赖

| 依赖包 | 版本要求 | 用途 | 是否必需 | 对应需求 |
|--------|----------|------|----------|----------|
| `requests` | >=2.28.0 | 腾讯行情港股接口HTTP请求 | 是（已有） | REQ-HK-009 |

> **结论：无新增依赖**。akshare、pandas、pyyaml、rich、requests均为现有依赖。akshare的港股接口已包含在现有版本中。

---

## **9.8 港股通需求追溯矩阵**

| 需求编号 | 需求描述 | 对应模块/接口 | 设计文档章节 |
|----------|----------|---------------|-------------|
| REQ-HK-001 | 港股通成分股获取 | HKIndexFetcher.fetch() | 9.2.2 |
| REQ-HK-002 | 沪港通+深港通合并去重 | HKIndexFetcher._merge_and_deduplicate() | 9.2.2 |
| REQ-HK-003 | 成分股获取失败终止 | HKIndexFetcher异常处理 | 9.5 |
| REQ-HK-004 | 港股资产负债表映射 | HKFinanceFetcher + FieldMapper | 9.2.3 |
| REQ-HK-005 | 港股有息负债计算 | FieldMapper._calc_interest_bearing_debt() | 9.2.3 |
| REQ-HK-006 | 港股利润表映射 | HKFinanceFetcher.fetch_income_statement() | 9.2.3 |
| REQ-HK-007 | 扣非净利润缺失处理 | HKFinanceFetcher + estimated标记 | 9.2.3 |
| REQ-HK-008 | 港股现金流量表映射 | HKFinanceFetcher.fetch_cash_flow() | 9.2.3 |
| REQ-HK-009 | 港股市值数据获取 | HKMarketFetcher.fetch_batch_market_data() | 9.2.4 |
| REQ-HK-010 | 市值数据缺失跳过 | HKMarketFetcher异常处理 | 9.2.4 |
| REQ-HK-011 | 港股分红数据获取 | HKDividendFetcher.fetch_dividend_data() | 9.2.5 |
| REQ-HK-012 | 仙→港元单位转换 | HKDividendFetcher._convert_cent_to_hkd() | 9.2.5 |
| REQ-HK-013 | 分红数据缺失默认值 | HKDividendFetcher异常处理 | 9.2.5 |
| REQ-HK-014 | 港币独立计价输出 | ScoredResult.currency + format | 9.2.10 |
| REQ-HK-015 | 汇率统一换算(可选) | CurrencyConverter | 9.2.11 |
| REQ-HK-016 | 港股退市风险过滤 | HKDelistingFilter.is_delisting_risk() | 9.2.6 |
| REQ-HK-017 | 港交所退市规则 | HKDelistingFilter四项过滤 | 9.2.6 |
| REQ-HK-018 | 退市整理期过滤 | HKDelistingFilter._check_delisting_period() | 9.2.6 |
| REQ-HK-019 | 无法判断时保留 | HKDelistingFilter警告日志 | 9.2.6 |
| REQ-HK-020 | 核心筛选逻辑复用 | AssetCushion/OperationSafety/RedemptionSafety/Scorer | 9.2.7 |
| REQ-HK-021 | 港股专用阈值覆盖 | _get_hk_asset_cushion_config() | 9.2.7 |
| REQ-HK-022 | 港股结果输出格式 | format_scored_result() + HK专属字段 | 9.2.10 |
| REQ-HK-023 | 港股独立CSV文件 | CsvWriter.write_hk() | 9.2.10 |
| REQ-HK-024 | A股/港股独立输出 | main.py市场路由 | 9.2.9 |
| REQ-HK-025 | market配置字段 | Settings.market | 9.2.8 |
| REQ-HK-026 | hk_stock配置区块 | HKStockConfig + config.yaml | 9.2.8 |
| REQ-HK-027 | 港股配置默认值 | HKStockConfig默认值 | 9.2.8 |
| REQ-HK-028 | 港股选股流程初始化 | run_hk_stock_selection() | 9.2.9 |
| REQ-HK-029 | ALL模式依次执行 | main.py市场路由 | 9.2.9 |
| REQ-HK-030 | A模式向后兼容 | run_a_stock_selection() | 9.2.9 |
| REQ-HK-031 | 启动输出市场标识 | main.py日志 | 9.2.9 |
| NFR-HK-001 | 8分钟完成 | 性能预估 | 9.6 |
| NFR-HK-002 | 字段映射配置化 | FieldMapper + hk_field_mapping.yaml | 9.2.3 |
| NFR-HK-003 | 字段名变更快速适配 | hk_field_mapping.yaml | 9.2.3 |
| NFR-HK-004 | analyzer层代码共享 | 完全复用设计 | 9.2.7 |
| NFR-HK-005 | 优先合并报表 | HKFinanceFetcher报表选择逻辑 | 9.2.3 |
