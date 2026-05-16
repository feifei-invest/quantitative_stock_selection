# 沪深300价值股票量化选股系统 — 编码任务分解文档

---

## 任务总览表

| 任务编号 | 任务名称 | 所属模块 | 关联需求 | 前置任务 | 优先级 | 预估工时 |
|----------|----------|----------|----------|----------|--------|----------|
| T01 | 项目基础设施搭建 | 项目根目录 | CON-001, CON-003 | 无 | P0 | 0.5h |
| T02 | Python依赖安装与验证 | 项目根目录 | CON-001, CON-002 | T01 | P0 | 0.5h |
| T03 | 自定义异常体系 | common/ | NFR-005 | T01 | P0 | 1h |
| T04 | 数据模型定义（枚举+基础模型） | common/ | REQ-001~004 | T01 | P0 | 1.5h |
| T05 | 数据模型定义（聚合+结果模型） | common/ | REQ-005~012, REQ-014 | T04 | P0 | 1h |
| T06 | 重试装饰器 | common/ | NFR-002 | T03 | P0 | 1h |
| T07 | 日志管理器 | common/ | NFR-003 | T01 | P0 | 1h |
| T08 | 配置文件模板与默认配置 | config/ | NFR-004 | T01 | P0 | 1h |
| T09 | 配置加载与校验（Settings单例） | config/ | NFR-004, CON-002 | T04, T08 | P0 | 1.5h |
| T10 | 数据获取基类BaseFetcher | fetcher/ | NFR-002, NFR-005 | T03, T06, T09 | P1 | 1.5h |
| T11 | 数据缓存管理DataCache | fetcher/ | NFR-001 | T09 | P1 | 1.5h |
| T12 | 沪深300成分股获取器IndexFetcher | fetcher/ | REQ-001 | T10, T11 | P1 | 1.5h |
| T13 | 财务数据获取器FinanceFetcher | fetcher/ | REQ-002, REQ-010 | T10, T11 | P1 | 2h |
| T14 | 市值数据获取器MarketFetcher | fetcher/ | REQ-003, NFR-001 | T10, T11 | P1 | 1.5h |
| T15 | 分红数据获取器DividendFetcher | fetcher/ | REQ-004 | T10, T11 | P1 | 1.5h |
| T16 | 退市风险过滤DelistingFilter | analyzer/ | REQ-013 | T05, T09 | P1 | 1.5h |
| T17 | 资产垫计算与分级AssetCushionAnalyzer | analyzer/ | REQ-005, REQ-006 | T05, T09 | P1 | 2h |
| T18 | 经营安全评估OperationSafetyAnalyzer | analyzer/ | REQ-007, REQ-008 | T05, T09 | P1 | 1.5h |
| T19 | 兑现安全评估RedemptionSafetyAnalyzer | analyzer/ | REQ-009, REQ-010 | T05, T09 | P1 | 2h |
| T20 | 综合评分与排序Scorer | analyzer/ | REQ-011, REQ-012 | T05, T09 | P1 | 1.5h |
| T21 | 数据格式化工具 | output/ | REQ-014 | T05 | P2 | 1h |
| T22 | CSV输出器CsvWriter | output/ | REQ-015 | T05, T21 | P2 | 1h |
| T23 | 终端表格输出器TablePrinter | output/ | REQ-015 | T05, T21 | P2 | 1h |
| T24 | 主程序入口与流程编排main.py | 入口层 | 全部REQ | T09, T12~T15, T16~T20, T22, T23 | P2 | 2h |
| T25 | 单元测试-业务逻辑层 | tests/ | REQ-005~013 | T16~T20 | P2 | 3h |
| T26 | 集成验证与端到端测试 | tests/ | 全部REQ, NFR-001 | T24 | P2 | 2h |

**总计：26个任务，预估总工时约 34.5 小时**

---

## 任务详细描述

---

### T01: 项目基础设施搭建

- **任务名称**：项目基础设施搭建
- **所属模块**：项目根目录
- **关联需求**：CON-001, CON-003
- **前置任务**：无
- **优先级**：P0
- **预估工时**：0.5h

- **任务描述**：
  创建项目完整目录结构，包括所有包的`__init__.py`文件和必要的空目录占位。

  具体创建：
  - `main.py` — 空文件占位
  - `config/` 目录及 `__init__.py`
  - `fetcher/` 目录及 `__init__.py`
  - `analyzer/` 目录及 `__init__.py`
  - `output/` 目录及 `__init__.py`
  - `common/` 目录及 `__init__.py`
  - `output_data/results/` 输出目录
  - `logs/` 日志目录
  - `tests/` 目录及 `__init__.py`

- **验收标准**：
  - 目录结构完整，所有`__init__.py`存在
  - `python -c "import common; import config; import fetcher; import analyzer; import output"` 无报错

---

### T02: Python依赖安装与验证

- **任务名称**：Python依赖安装与验证
- **所属模块**：项目根目录
- **关联需求**：CON-001, CON-002
- **前置任务**：T01
- **优先级**：P0
- **预估工时**：0.5h

- **任务描述**：
  创建 `requirements.txt` 并安装所有Python依赖包，验证各包可正常导入。

  具体内容：
  - 创建 `requirements.txt`，包含：
    - `akshare>=1.14.0`
    - `pandas>=2.0.0`
    - `pyyaml>=6.0`
    - `rich>=13.0.0`
  - 使用 `pip install -r requirements.txt` 安装依赖
  - 验证 `import akshare`, `import pandas`, `import yaml`, `import rich` 均成功

- **验收标准**：
  - `requirements.txt` 文件存在且内容正确
  - 所有依赖包安装成功，import验证通过
  - Python版本为 3.10+

---

### T03: 自定义异常体系

- **任务名称**：自定义异常体系
- **所属模块**：`common/exceptions.py`
- **关联需求**：NFR-005
- **前置任务**：T01
- **优先级**：P0
- **预估工时**：1h

- **任务描述**：
  在 `common/exceptions.py` 中实现完整的自定义异常类层级：

  - `StockSelectionError(Exception)` — 系统基础异常
  - `DataFetchError(StockSelectionError)` — 数据获取异常，含 `stock_code` 和 `data_type` 属性
  - `DataMissingError(StockSelectionError)` — 数据缺失异常，含 `stock_code` 和 `missing_fields` 属性
  - `DataValidationError(StockSelectionError)` — 数据校验异常（如市值为0导致比率计算异常）
  - `ConfigError(StockSelectionError)` — 配置加载异常
  - `RateLimitError(DataFetchError)` — API限流异常

  每个异常类需实现 `__str__` 方法，返回包含关键信息的可读错误描述。

- **验收标准**：
  - 所有6个异常类均可正常实例化与抛出
  - 异常继承关系正确：`RateLimitError` → `DataFetchError` → `StockSelectionError`
  - `__str__` 输出包含 stock_code、data_type 等关键信息

---

### T04: 数据模型定义（枚举+基础模型）

- **任务名称**：数据模型定义（枚举+基础数据模型）
- **所属模块**：`common/models.py`
- **关联需求**：REQ-001, REQ-002, REQ-003, REQ-004
- **前置任务**：T01
- **优先级**：P0
- **预估工时**：1.5h

- **任务描述**：
  在 `common/models.py` 中定义枚举类型和基础数据模型：

  **枚举类型**：
  - `AssetCushionTier(Enum)` — 资产垫等级：T0, T1, T2, FAIL
  - `OperationStatus(Enum)` — 经营安全状态：PASS, PARTIAL, FAIL
  - `RedemptionPath(Enum)` — 兑现路径类型：DIVIDEND, EVENT, EARNINGS_RECOVERY, NONE

  **基础数据模型（dataclass）**：
  - `StockInfo` — 股票基本信息：code, name, exchange
  - `BalanceSheet` — 资产负债表：cash_and_equivalents, total_current_assets, total_assets, total_current_liabilities, total_liabilities, interest_bearing_debt, net_assets
  - `IncomeStatement` — 利润表：revenue, operating_cost, net_profit, deducted_net_profit
  - `CashFlowStatement` — 现金流量表：operating_cash_flow, capital_expenditure, free_cash_flow
  - `MarketData` — 市值数据：total_market_cap, circulating_market_cap, latest_price
  - `DividendData` — 分红数据：total_cash_dividend_3y, dividend_yield, dividend_years

  所有金融数值使用 `float`，金额单位为元，比率使用小数。

- **验收标准**：
  - 所有枚举类型可正常使用，成员值与设计文档一致
  - 所有dataclass可正常实例化，字段完整
  - 类型注解正确，可被mypy检查通过

---

### T05: 数据模型定义（聚合+结果模型）

- **任务名称**：数据模型定义（聚合+结果模型）
- **所属模块**：`common/models.py`
- **关联需求**：REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012, REQ-014
- **前置任务**：T04
- **优先级**：P0
- **预估工时**：1h

- **任务描述**：
  在 `common/models.py` 中补充聚合数据模型和业务结果模型：

  **聚合模型**：
  - `StockFullData` — 股票完整数据：info, balance, income, cash_flow, market, dividend, multi_year_deducted_profits, is_data_complete, missing_fields

  **业务结果模型**：
  - `AssetCushionResult` — 资产垫评估结果：conservative_cash_net, loose_cash_net, conservative_ratio, loose_ratio, current_asset_net_ratio, tier
  - `OperationSafetyResult` — 经营安全评估结果：free_cash_flow, capex_ratio, is_fcf_positive, is_capex_ratio_low, status
  - `RedemptionSafetyResult` — 兑现安全评估结果：dividend_path, event_path, earnings_path, has_redemption_logic, path_type
  - `ScoredResult` — 综合评分结果：stock_code, stock_name, asset_cushion_tier, conservative_ratio, loose_ratio, free_cash_flow, capex_ratio, redemption_path_type, asset_cushion_score, operation_safety_score, redemption_safety_score, total_score, rank

- **验收标准**：
  - 所有聚合和结果模型可正常实例化
  - `StockFullData` 包含 is_data_complete 和 missing_fields 字段
  - `ScoredResult` 包含 rank 字段且默认值为0
  - 所有模型字段类型注解正确

---

### T06: 重试装饰器

- **任务名称**：重试装饰器
- **所属模块**：`common/retry.py`
- **关联需求**：NFR-002
- **前置任务**：T03
- **优先级**：P0
- **预估工时**：1h

- **任务描述**：
  在 `common/retry.py` 中实现 `retry_on_failure` 装饰器：

  - 参数：`max_attempts`（默认3）、`interval_seconds`（默认5.0）、`retryable_exceptions`（默认 DataFetchError, RateLimitError）
  - 实现指数退避策略：每次重试间隔递增（5s, 10s, 20s）
  - 每次重试记录WARNING级别日志（含重试次数、异常信息、下次等待时间）
  - 超过最大重试次数后抛出最后一次异常
  - 非retryable异常不重试，直接抛出

- **验收标准**：
  - 装饰器可正常装饰同步函数
  - 重试次数不超过 max_attempts
  - 指数退避间隔正确
  - 非retryable异常直接抛出
  - 重试过程中有日志输出

---

### T07: 日志管理器

- **任务名称**：日志管理器
- **所属模块**：`common/logger.py`
- **关联需求**：NFR-003
- **前置任务**：T01
- **优先级**：P0
- **预估工时**：1h

- **任务描述**：
  在 `common/logger.py` 中实现 `LoggerManager`：

  - `setup(log_dir, log_level="INFO") -> logging.Logger` 静态方法
  - 同时输出到终端（StreamHandler）和文件（FileHandler）
  - 日志文件按日期命名，格式：`stock_selection_YYYYMMDD.log`
  - 日志格式：`%(asctime)s - %(name)s - %(levelname)s - %(message)s`
  - 终端输出使用简洁格式，文件输出使用完整格式
  - 确保日志目录存在（自动创建）
  - 设置UTF-8编码，避免中文乱码

- **验收标准**：
  - 调用 `LoggerManager.setup()` 返回有效的 Logger 实例
  - 日志同时输出到终端和文件
  - 日志文件在指定目录下按日期命名
  - 中文日志内容不乱码

---

### T08: 配置文件模板与默认配置

- **任务名称**：配置文件模板与默认配置
- **所属模块**：`config/default_config.yaml`, `config.yaml`
- **关联需求**：NFR-004
- **前置任务**：T01
- **优先级**：P0
- **预估工时**：1h

- **任务描述**：
  创建配置文件，定义所有可调参数的默认值：

  - 创建 `config/default_config.yaml` — 默认配置模板，包含完整注释
  - 创建 `config.yaml` — 用户配置文件（初始复制默认配置）

  配置项包括：
  - `data_source` — 数据源配置（primary, fallback, retry, cache）
  - `delisting` — 退市风险过滤阈值（st_keywords, min_revenue, require_positive_net_assets）
  - `asset_cushion` — 资产垫分级阈值（t0, t1, t2各条件）
  - `operation_safety` — 经营安全阈值（require_positive_fcf, max_capex_ratio）
  - `redemption_safety` — 兑现安全阈值（dividend, earnings_recovery）
  - `scoring` — 综合评分权重与分值
  - `output` — 输出配置（csv_dir, csv_encoding, log_dir, log_level, terminal_max_rows）

  所有值需与设计文档1.3.1节完全一致。

- **验收标准**：
  - `config.yaml` 和 `config/default_config.yaml` 均存在
  - YAML语法正确，可被 `yaml.safe_load()` 正常解析
  - 所有配置项与设计文档一致，含完整中文注释

---

### T09: 配置加载与校验（Settings单例）

- **任务名称**：配置加载与校验（Settings单例）
- **所属模块**：`config/settings.py`
- **关联需求**：NFR-004, CON-002
- **前置任务**：T04, T08
- **优先级**：P0
- **预估工时**：1.5h

- **任务描述**：
  在 `config/settings.py` 中实现配置加载与校验逻辑：

  **配置dataclass**：
  - `DataSourceConfig` — data_source 配置
  - `DelistingConfig` — delisting 配置
  - `AssetCushionConfig` — asset_cushion 配置（含 t0/t1/t2 子配置）
  - `OperationSafetyConfig` — operation_safety 配置
  - `RedemptionSafetyConfig` — redemption_safety 配置（含 dividend/earnings_recovery 子配置）
  - `ScoringConfig` — scoring 配置
  - `OutputConfig` — output 配置

  **Settings单例类**：
  - `load(config_path="config.yaml") -> Settings` — 从YAML加载配置
  - `get() -> Settings` — 获取已加载的单例
  - 加载时若config.yaml不存在，回退到default_config.yaml并记录WARNING
  - 配置值校验：权重之和为1.0，比率值在合理范围，缺失字段用默认值填充
  - 校验失败时抛出 `ConfigError`

- **验收标准**：
  - `Settings.load()` 可正常加载 config.yaml
  - config.yaml 不存在时回退到 default_config.yaml
  - 单例模式正确，多次调用返回同一实例
  - 配置值校验生效，权重和为1.0
  - 校验失败抛出 ConfigError

---

### T10: 数据获取基类BaseFetcher

- **任务名称**：数据获取基类BaseFetcher
- **所属模块**：`fetcher/base_fetcher.py`
- **关联需求**：NFR-002, NFR-005
- **前置任务**：T03, T06, T09
- **优先级**：P1
- **预估工时**：1.5h

- **任务描述**：
  在 `fetcher/base_fetcher.py` 中实现数据获取基类：

  - `BaseFetcher(ABC)` 抽象基类
  - `__init__(self, settings: Settings)` — 初始化配置和日志
  - `fetch(self, *args, **kwargs) -> Any` — 抽象方法，子类实现实际获取逻辑
  - `fetch_with_retry(self, *args, **kwargs) -> Any` — 带重试机制的获取方法，内部调用 `retry_on_failure` 装饰的逻辑
  - `_handle_data_missing(self, stock_code: str, field: str) -> None` — 数据缺失处理，记录日志并抛出 `DataMissingError`
  - `_validate_data(self, data: dict, required_fields: list[str], stock_code: str) -> dict` — 数据校验，检查必填字段是否存在
  - 请求间隔控制：每次API请求后 sleep 0.2秒，避免触发限流

- **验收标准**：
  - BaseFetcher 不可直接实例化（抽象类）
  - fetch_with_retry 在失败时自动重试
  - _handle_data_missing 抛出 DataMissingError
  - 子类继承后只需实现 fetch 方法

---

### T11: 数据缓存管理DataCache

- **任务名称**：数据缓存管理DataCache
- **所属模块**：`fetcher/data_cache.py`
- **关联需求**：NFR-001
- **前置任务**：T09
- **优先级**：P1
- **预估工时**：1.5h

- **任务描述**：
  在 `fetcher/data_cache.py` 中实现基于磁盘的JSON缓存管理：

  - `DataCache` 类
  - `__init__(self, cache_dir: str, expire_hours: int = 4)` — 初始化缓存目录和过期时间
  - `get(self, cache_key: str) -> dict | None` — 获取缓存数据，过期返回None
  - `set(self, cache_key: str, data: dict, expire_hours: int | None = None) -> None` — 写入缓存
  - `is_expired(self, cache_key: str) -> bool` — 判断缓存是否过期
  - `clear_all(self) -> None` — 清空所有缓存
  - 缓存键格式：`{data_type}_{stock_code}_{date}`
  - 缓存文件格式：JSON，包含 `data`、`timestamp`、`expire_hours` 字段
  - 自动创建缓存目录
  - 财动数据缓存期4小时（季报），行情数据缓存期1小时（日更）

- **验收标准**：
  - 缓存写入后可正确读取
  - 过期缓存返回None
  - clear_all 清空所有缓存文件
  - 缓存目录不存在时自动创建

---

### T12: 沪深300成分股获取器IndexFetcher

- **任务名称**：沪深300成分股获取器IndexFetcher
- **所属模块**：`fetcher/index_fetcher.py`
- **关联需求**：REQ-001
- **前置任务**：T10, T11
- **优先级**：P1
- **预估工时**：1.5h

- **任务描述**：
  在 `fetcher/index_fetcher.py` 中实现沪深300成分股获取：

  - `IndexFetcher(BaseFetcher)` 类
  - `fetch_hs300_constituents(self) -> list[StockInfo]` — 获取沪深300全部成分股
  - 主数据源：`akshare.index_stock_cs300()` 接口
  - 解析返回的DataFrame，提取股票代码、名称
  - 根据股票代码判断交易所（6开头为SH，0/3开头为SZ）
  - 数据缓存：成分股列表缓存1小时
  - 异常处理：akshare接口失败时记录错误日志，尝试备选方案（暂仅支持akshare）
  - 返回结果按股票代码排序

- **验收标准**：
  - 调用返回 list[StockInfo]，长度约300
  - StockInfo 包含正确的 code、name、exchange
  - 交易所判断正确（SH/SZ）
  - 接口失败时有错误日志且不崩溃

---

### T13: 财务数据获取器FinanceFetcher

- **任务名称**：财务数据获取器FinanceFetcher
- **所属模块**：`fetcher/finance_fetcher.py`
- **关联需求**：REQ-002, REQ-010
- **前置任务**：T10, T11
- **优先级**：P1
- **预估工时**：2h

- **任务描述**：
  在 `fetcher/finance_fetcher.py` 中实现财务数据获取：

  - `FinanceFetcher(BaseFetcher)` 类
  - `fetch_balance_sheet(self, stock_code: str) -> BalanceSheet` — 获取资产负债表
    - 数据源：`akshare.stock_balance_sheet_by_report_em(symbol=code)`
    - 提取字段：现金及等价物、流动资产、总资产、流动负债、总负债、有息负债（短期借款+长期借款+应付债券）、净资产
  - `fetch_income_statement(self, stock_code: str) -> IncomeStatement` — 获取利润表
    - 数据源：`akshare.stock_profit_sheet_by_report_em(symbol=code)`
    - 提取字段：营业收入、营业成本、净利润、扣非净利润
  - `fetch_cash_flow(self, stock_code: str) -> CashFlowStatement` — 获取现金流量表
    - 数据源：`akshare.stock_cash_flow_statement_by_report_em(symbol=code)`
    - 提取字段：经营活动现金流、资本开支，并计算自由现金流
  - `fetch_multi_year_deducted_profit(self, stock_code: str, years: int = 3) -> list[float]` — 获取近N年扣非净利润
    - 用于盈利恢复兑现路径判断 (REQ-010)
  - 所有方法需处理akshare返回DataFrame的字段映射
  - 数据缓存：财报数据缓存4小时
  - 数据缺失时标注 missing_fields 并设置 is_data_complete=False

- **验收标准**：
  - 三张财务报表方法返回正确的dataclass实例
  - 字段映射正确，有息负债计算为短期借款+长期借款+应付债券
  - 自由现金流 = 经营现金流 - 资本开支
  - multi_year_deducted_profit 返回近3年数据
  - 数据缺失时 missing_fields 非空

---

### T14: 市值数据获取器MarketFetcher

- **任务名称**：市值数据获取器MarketFetcher
- **所属模块**：`fetcher/market_fetcher.py`
- **关联需求**：REQ-003, NFR-001
- **前置任务**：T10, T11
- **优先级**：P1
- **预估工时**：1.5h

- **任务描述**：
  在 `fetcher/market_fetcher.py` 中实现市值数据获取：

  - `MarketFetcher(BaseFetcher)` 类
  - `fetch_market_data(self, stock_code: str) -> MarketData` — 获取单只股票市值
  - `fetch_batch_market_data(self, stock_codes: list[str]) -> dict[str, MarketData]` — 批量获取市值（性能优化核心）
    - 数据源：`akshare.stock_zh_a_spot_em()` 单次返回全A股实时行情
    - 内存过滤沪深300成分股，避免300次单独请求
    - 提取字段：总市值、流通市值、最新股价
  - 市值数据缓存1小时
  - 处理市值为0的异常情况（跳过该股，记录WARNING）

- **验收标准**：
  - 单只和批量获取均返回正确的 MarketData 实例
  - 批量获取性能显著优于逐只获取（1次请求替代300次）
  - 市值为0时不崩溃，有WARNING日志
  - 数据缓存1小时生效

---

### T15: 分红数据获取器DividendFetcher

- **任务名称**：分红数据获取器DividendFetcher
- **所属模块**：`fetcher/dividend_fetcher.py`
- **关联需求**：REQ-004
- **前置任务**：T10, T11
- **优先级**：P1
- **预估工时**：1.5h

- **任务描述**：
  在 `fetcher/dividend_fetcher.py` 中实现分红数据获取：

  - `DividendFetcher(BaseFetcher)` 类
  - `fetch_dividend_data(self, stock_code: str) -> DividendData` — 获取分红数据
    - 数据源：`akshare.stock_dividend_cn(symbol=code)` 或其他分红接口
    - 计算近3年累计现金分红金额
    - 计算近3年分红年数
    - 计算股息率（近3年均分红 / 当前股价）
  - 处理无分红记录的情况（返回 DividendData 全零值）
  - 分红数据缓存4小时

- **验收标准**：
  - 返回正确的 DividendData 实例
  - 近3年分红年数和累计金额计算正确
  - 无分红记录时返回全零值，不崩溃
  - 股息率计算公式正确

---

### T16: 退市风险过滤DelistingFilter

- **任务名称**：退市风险过滤DelistingFilter
- **所属模块**：`analyzer/delisting_filter.py`
- **关联需求**：REQ-013
- **前置任务**：T05, T09
- **优先级**：P1
- **预估工时**：1.5h

- **任务描述**：
  在 `analyzer/delisting_filter.py` 中实现退市风险过滤：

  - `DelistingFilter` 类
  - `__init__(self, config: DelistingConfig)` — 接收配置
  - `is_delisting_risk(self, stock: StockFullData) -> bool` — 判断是否存在退市风险
  - `filter(self, stocks: list[StockFullData]) -> list[StockFullData]` — 批量过滤
  - `_check_st_status(self, stock_name: str) -> bool` — 检查ST标记（包含"ST"或"*ST"）
  - `_check_financial_risk(self, deducted_profit: float, revenue: float) -> bool` — 检查财务退市风险（扣非净利润为负 且 营业收入 < 1亿元）
  - `_check_negative_assets(self, net_assets: float) -> bool` — 检查净资产为负
  - 任一条件满足即判定为退市风险
  - 过滤时记录每只被剔除股票的原因

- **验收标准**：
  - ST股票被正确识别并过滤
  - 扣非净利润为负且营收<1亿的股票被过滤
  - 净资产为负的股票被过滤
  - 过滤日志包含每只被剔除股票的具体原因
  - 正常股票不受影响

---

### T17: 资产垫计算与分级AssetCushionAnalyzer

- **任务名称**：资产垫计算与分级AssetCushionAnalyzer
- **所属模块**：`analyzer/asset_cushion.py`
- **关联需求**：REQ-005, REQ-006
- **前置任务**：T05, T09
- **优先级**：P1
- **预估工时**：2h

- **任务描述**：
  在 `analyzer/asset_cushion.py` 中实现资产垫计算与分级：

  - `AssetCushionAnalyzer` 类
  - `__init__(self, config: AssetCushionConfig)` — 接收配置
  - `calculate(self, stock: StockFullData) -> AssetCushionResult` — 计算资产垫指标并分级

  **核心计算 (REQ-005)**：
  - 保守现金净额 = 现金及等价物 - 总负债
  - 宽松现金净额 = 现金及等价物 - 有息负债
  - 保守资产垫比率 = 保守现金净额 / 总市值
  - 宽松资产垫比率 = 宽松现金净额 / 总市值
  - 流动资产净值比率 = (流动资产 - 总负债) / 总市值

  **分级规则 (REQ-006)**：
  - T0：保守比率 >= 0.8 且 宽松比率 >= 1.5
  - T1：宽松比率 >= 1.0 且 保守现金净额 > 0
  - T2：宽松现金净额 > 0 且 流动资产净值比率 > 0.5
  - FAIL：不满足以上任何条件

  - `_classify_tier(self, result: AssetCushionResult) -> AssetCushionTier` — 分级判定
  - 所有阈值从配置读取，不硬编码
  - 总市值为0时抛出 DataValidationError

- **验收标准**：
  - 资产垫指标计算公式正确
  - T0/T1/T2/FAIL 分级判定逻辑正确
  - 阈值从配置读取，修改配置后结果变化
  - 市值为0时不崩溃

---

### T18: 经营安全评估OperationSafetyAnalyzer

- **任务名称**：经营安全评估OperationSafetyAnalyzer
- **所属模块**：`analyzer/operation_safety.py`
- **关联需求**：REQ-007, REQ-008
- **前置任务**：T05, T09
- **优先级**：P1
- **预估工时**：1.5h

- **任务描述**：
  在 `analyzer/operation_safety.py` 中实现经营安全评估：

  - `OperationSafetyAnalyzer` 类
  - `__init__(self, config: OperationSafetyConfig)` — 接收配置
  - `evaluate(self, stock: StockFullData) -> OperationSafetyResult` — 评估经营安全

  **计算指标 (REQ-007)**：
  - 自由现金流 = 经营现金流 - 资本开支
  - 资本开支率 = 资本开支 / 经营现金流

  **判定条件 (REQ-008)**：
  - PASS：自由现金流 > 0 且 资本开支率 < 0.5
  - PARTIAL：自由现金流 > 0 但 资本开支率 >= 0.5
  - FAIL：自由现金流 <= 0

  - 经营现金流为0时，资本开支率设为无穷大，状态为FAIL
  - 阈值从配置读取

- **验收标准**：
  - 自由现金流和资本开支率计算正确
  - PASS/PARTIAL/FAIL 三种状态判定逻辑正确
  - 经营现金流为0时不崩溃，状态为FAIL
  - 阈值从配置读取

---

### T19: 兑现安全评估RedemptionSafetyAnalyzer

- **任务名称**：兑现安全评估RedemptionSafetyAnalyzer
- **所属模块**：`analyzer/redemption_safety.py`
- **关联需求**：REQ-009, REQ-010
- **前置任务**：T05, T09
- **优先级**：P1
- **预估工时**：2h

- **任务描述**：
  在 `analyzer/redemption_safety.py` 中实现兑现安全评估：

  - `RedemptionSafetyAnalyzer` 类
  - `__init__(self, config: RedemptionSafetyConfig)` — 接收配置
  - `evaluate(self, stock: StockFullData) -> RedemptionSafetyResult` — 评估兑现安全

  **三条兑现路径 (REQ-009)**：
  - `_check_dividend_path(self, dividend: DividendData) -> bool` — 分红兑现路径
    - 条件：近3年分红年数 >= 3 且 平均股息率 > 2%
  - `_check_event_path(self, stock_code: str) -> bool` — 事件兑现路径
    - 初版默认返回False（数据源有限，后续扩展）
  - `_check_earnings_path(self, deducted_profits: list[float]) -> bool` — 盈利恢复兑现路径 (REQ-010)
    - 条件：近3年扣非净利润均为正 且 最近一年 > 前一年

  - has_redemption_logic = dividend_path or event_path or earnings_path
  - path_type 为满足的路径描述（多条路径用逗号分隔）

- **验收标准**：
  - 分红兑现路径判断正确（3年持续分红且股息率>2%）
  - 事件兑现路径默认返回False
  - 盈利恢复兑现路径判断正确（3年为正且递增）
  - 多条路径同时满足时 path_type 包含所有路径
  - 无兑现路径时 has_redemption_logic=False, path_type="无"

---

### T20: 综合评分与排序Scorer

- **任务名称**：综合评分与排序Scorer
- **所属模块**：`analyzer/scorer.py`
- **关联需求**：REQ-011, REQ-012
- **前置任务**：T05, T09
- **优先级**：P1
- **预估工时**：1.5h

- **任务描述**：
  在 `analyzer/scorer.py` 中实现综合评分与排序：

  - `Scorer` 类
  - `__init__(self, config: ScoringConfig)` — 接收配置

  **评分规则 (REQ-011)**：
  - `score(self, stock, asset_result, operation_result, redemption_result) -> ScoredResult`
  - 资产垫得分：T0=100, T1=70, T2=40, FAIL=0
  - 经营安全得分：PASS=100, PARTIAL=50, FAIL=0
  - 兑现安全得分：有兑现逻辑=100, 无=0
  - 综合分 = 资产垫得分 × 40% + 经营安全得分 × 30% + 兑现安全得分 × 30%

  **排序 (REQ-012)**：
  - `rank(self, results: list[ScoredResult]) -> list[ScoredResult]`
  - 按综合得分从高到低排序
  - 设置 rank 字段（1, 2, 3...）
  - 同分时按资产垫等级排序（T0 > T1 > T2）

  - 所有权重和分值从配置读取

- **验收标准**：
  - 综合评分计算公式正确，权重之和为1.0
  - 各维度得分映射正确
  - 排序按综合分降序，同分时按资产垫等级排序
  - rank 字段正确设置（从1开始）
  - 权重和分值从配置读取

---

### T21: 数据格式化工具

- **任务名称**：数据格式化工具
- **所属模块**：`output/formatter.py`
- **关联需求**：REQ-014
- **前置任务**：T05
- **优先级**：P2
- **预估工时**：1h

- **任务描述**：
  在 `output/formatter.py` 中实现数据格式化工具：

  - `format_money(value: float) -> str` — 金额格式化（亿元单位，保留2位小数，如"12.34亿"）
  - `format_ratio(value: float) -> str` — 比率格式化（百分比形式，保留2位小数，如"56.78%"）
  - `format_score(value: float) -> str` — 评分格式化（保留1位小数）
  - `format_tier(tier: AssetCushionTier) -> str` — 资产垫等级格式化
  - `format_status(status: OperationStatus) -> str` — 经营安全状态格式化
  - 处理None和NaN值，返回"-"

- **验收标准**：
  - 金额正确格式化为亿元单位
  - 比率正确格式化为百分比
  - None/NaN 处理为"-"
  - 各格式化函数可独立调用

---

### T22: CSV输出器CsvWriter

- **任务名称**：CSV输出器CsvWriter
- **所属模块**：`output/csv_writer.py`
- **关联需求**：REQ-015
- **前置任务**：T05, T21
- **优先级**：P2
- **预估工时**：1h

- **任务描述**：
  在 `output/csv_writer.py` 中实现CSV文件输出：

  - `CsvWriter` 类
  - `__init__(self, output_dir: str, encoding: str = "utf-8-sig")` — 初始化输出目录和编码
  - `write(self, results: list[ScoredResult], filename: str | None = None) -> str` — 写入CSV文件

  **输出字段 (REQ-014)**：
  - 排名、股票代码、股票名称、资产垫等级、资产垫比率(保守)、资产垫比率(宽松)、自由现金流、资本开支率、兑现逻辑类型、资产垫得分、经营安全得分、兑现安全得分、综合评分

  - 文件名默认：`hs300_value_stocks_YYYYMMDD_HHmmss.csv`
  - 编码：utf-8-sig（Excel兼容中文）
  - 自动创建输出目录
  - 使用 pandas DataFrame 写入 CSV

- **验收标准**：
  - CSV文件正确生成，包含所有13个字段
  - 中文内容在Excel中正常显示
  - 文件名包含日期时间戳
  - 输出目录不存在时自动创建

---

### T23: 终端表格输出器TablePrinter

- **任务名称**：终端表格输出器TablePrinter
- **所属模块**：`output/table_printer.py`
- **关联需求**：REQ-015
- **前置任务**：T05, T21
- **优先级**：P2
- **预估工时**：1h

- **任务描述**：
  在 `output/table_printer.py` 中实现终端表格输出：

  - `TablePrinter` 类
  - `__init__(self, max_rows: int = 50)` — 限制终端显示行数
  - `print(self, results: list[ScoredResult]) -> None` — 打印终端表格

  - 使用 rich 库的 Table 组件
  - 表格标题：沪深300价值选股结果
  - 列：排名、代码、名称、资产垫等级、保守比率、宽松比率、FCF、资本开支率、兑现路径、综合评分
  - 资产垫等级颜色：T0绿色、T1黄色、T2蓝色、FAIL灰色
  - 综合评分颜色：>=80绿色、>=50黄色、<50红色
  - 超过max_rows时仅显示前max_rows行，并提示剩余数量

- **验收标准**：
  - 终端输出美观的表格
  - 颜色标记正确
  - 超过max_rows时截断显示
  - rich库正常工作

---

### T24: 主程序入口与流程编排main.py

- **任务名称**：主程序入口与流程编排main.py
- **所属模块**：`main.py`
- **关联需求**：全部REQ, NFR-001, NFR-005
- **前置任务**：T09, T12, T13, T14, T15, T16, T17, T18, T19, T20, T22, T23
- **优先级**：P2
- **预估工时**：2h

- **任务描述**：
  在 `main.py` 中实现完整的选股流程编排：

  **执行流程**：
  1. 加载配置 — `Settings.load("config.yaml")`
  2. 初始化日志 — `LoggerManager.setup()`
  3. 获取沪深300成分股 — `IndexFetcher.fetch_hs300_constituents()`
  4. 批量获取财务数据 — FinanceFetcher, MarketFetcher, DividendFetcher 逐只获取
  5. 退市风险过滤 — `DelistingFilter.filter()`
  6. 逐股评估三要义：
     - 资产垫计算与分级
     - 经营安全评估
     - 兑现安全评估
  7. 综合评分与排序 — `Scorer.score()` + `Scorer.rank()`
  8. 输出结果 — CsvWriter + TablePrinter

  **异常处理**：
  - 单股数据获取失败时记录WARNING并跳过，不影响其他股票 (NFR-005)
  - 整体流程异常时记录ERROR日志
  - 使用 try-except 包裹每只股票的处理逻辑

  **性能优化**：
  - 市值数据使用批量获取
  - 添加进度提示（如"正在获取第X/300只..."）

  - 添加 `if __name__ == "__main__": main()` 入口

- **验收标准**：
  - 完整流程可执行，从获取成分股到输出结果
  - 单股失败不中断整体流程
  - 有进度提示
  - 最终输出CSV文件和终端表格
  - 总耗时 < 5分钟 (NFR-001)

---

### T25: 单元测试-业务逻辑层

- **任务名称**：单元测试-业务逻辑层
- **所属模块**：`tests/`
- **关联需求**：REQ-005~013
- **前置任务**：T16, T17, T18, T19, T20
- **优先级**：P2
- **预估工时**：3h

- **任务描述**：
  在 `tests/` 目录下编写业务逻辑层的单元测试：

  - `test_delisting_filter.py` — 测试退市风险过滤：
    - 测试ST标记识别（含"ST"、含"*ST"、不含ST）
    - 测试财务退市风险判定
    - 测试净资产为负判定
    - 测试批量过滤逻辑

  - `test_asset_cushion.py` — 测试资产垫计算与分级：
    - 测试保守/宽松现金净额计算
    - 测试T0/T1/T2/FAIL各等级分级
    - 测试边界条件（比率为0、市值为0）

  - `test_operation_safety.py` — 测试经营安全评估：
    - 测试自由现金流和资本开支率计算
    - 测试PASS/PARTIAL/FAIL状态判定
    - 测试经营现金流为0的特殊处理

  - `test_redemption_safety.py` — 测试兑现安全评估：
    - 测试分红兑现路径判定
    - 测试盈利恢复兑现路径判定
    - 测试多路径同时满足
    - 测试无兑现路径

  - `test_scorer.py` — 测试综合评分与排序：
    - 测试评分计算（各维度得分和综合分）
    - 测试排序逻辑
    - 测试同分排序规则

  使用 pytest 框架，构造测试数据无需依赖真实API。

- **验收标准**：
  - 所有测试用例通过
  - 覆盖正常流程、边界条件、异常情况
  - 测试数据为构造的mock数据，不依赖外部API
  - 使用 pytest 可一键运行

---

### T26: 集成验证与端到端测试

- **任务名称**：集成验证与端到端测试
- **所属模块**：`tests/`
- **关联需求**：全部REQ, NFR-001
- **前置任务**：T24
- **优先级**：P2
- **预估工时**：2h

- **任务描述**：
  进行集成验证和端到端测试：

  - 运行 `python main.py` 完整流程，验证：
    - 成分股获取正常（约300只）
    - 财务数据获取正常（检查输出日志）
    - 退市风险过滤生效（检查被过滤的股票）
    - 资产垫分级结果合理
    - 经营安全评估结果合理
    - 兑现安全评估结果合理
    - 综合评分和排序正确
    - CSV文件正常生成且可打开
    - 终端表格正常显示
  - 验证性能：总耗时 < 5分钟
  - 验证配置化：修改config.yaml中阈值，结果相应变化
  - 验证异常处理：模拟网络异常，确认重试机制和跳过逻辑
  - 验证数据缺失处理：部分数据缺失时不中断

- **验收标准**：
  - 完整流程端到端运行成功
  - CSV文件内容正确，字段完整
  - 终端表格显示正常
  - 总耗时 < 5分钟
  - 配置修改后结果变化
  - 异常情况不崩溃

---

## 任务依赖关系图

```
T01 (基础设施)
├── T02 (依赖安装)
├── T03 (异常体系) ──→ T06 (重试装饰器)
├── T04 (基础模型) ──→ T05 (聚合+结果模型)
├── T07 (日志管理)
└── T08 (配置模板) ──→ T09 (Settings单例)
                         ├── T10 (BaseFetcher) ──→ T11 (DataCache) ──┬── T12 (IndexFetcher)
                         │                                            ├── T13 (FinanceFetcher)
                         │                                            ├── T14 (MarketFetcher)
                         │                                            └── T15 (DividendFetcher)
                         ├── T16 (退市过滤)  ──┐
                         ├── T17 (资产垫)    ──┤
                         ├── T18 (经营安全)  ──┤── T24 (main.py) ──→ T26 (集成测试)
                         ├── T19 (兑现安全)  ──┤
                         └── T20 (综合评分)  ──┘
T05 (聚合+结果模型) ──→ T21 (格式化) ──┬── T22 (CSV输出)  ──→ T24
                                       └── T23 (表格输出) ──→ T24
T16~T20 (业务逻辑) ──→ T25 (单元测试)
```

---

## 需求覆盖追溯矩阵

| 需求编号 | 需求描述 | 覆盖任务 |
|----------|----------|----------|
| REQ-001 | 获取沪深300成分股 | T12 |
| REQ-002 | 财务数据采集 | T13 |
| REQ-003 | 市值数据获取 | T14 |
| REQ-004 | 分红数据获取 | T15 |
| REQ-005 | 资产垫指标计算 | T17 |
| REQ-006 | 资产垫分级(T0/T1/T2) | T17 |
| REQ-007 | 经营安全指标计算 | T18 |
| REQ-008 | 经营安全筛选条件 | T18 |
| REQ-009 | 兑现安全评估 | T19 |
| REQ-010 | 盈利恢复兑现判断 | T19 |
| REQ-011 | 综合评分 | T20 |
| REQ-012 | 结果排序 | T20 |
| REQ-013 | 退市风险过滤 | T16 |
| REQ-014 | 结果输出内容 | T05, T21, T22, T23 |
| REQ-015 | CSV+终端输出 | T22, T23 |
| NFR-001 | 5分钟完成 | T11, T14, T24, T26 |
| NFR-002 | 重试机制 | T06, T10 |
| NFR-003 | 运行日志 | T07 |
| NFR-004 | 阈值可配置化 | T08, T09 |
| NFR-005 | 数据缺失不中断 | T03, T10, T24 |
| CON-001 | Python 3.10+ | T02 |
| CON-002 | akshare优先 | T09, T10 |
| CON-003 | Windows+Anaconda | T01, T02 |
| CON-004 | 不使用付费接口 | T02, T12~T15 |
| CON-005 | 仅输出不交易 | T24 |

---

# 港股通选股功能扩展 — 编码任务分解文档

---

## 港股通任务总览表

| 任务编号 | 任务名称 | 所属模块 | 关联需求 | 前置任务 | 优先级 | 预估工时 |
|----------|----------|----------|----------|----------|--------|----------|
| HK-T01 | 数据模型扩展（market/currency字段） | common/ | REQ-HK-022, REQ-HK-014 | T05 | P0 | 1h |
| HK-T02 | 港股字段映射配置hk_field_mapping.yaml | config/ | NFR-HK-002, NFR-HK-003 | T09 | P0 | 1h |
| HK-T03 | 港股配置类扩展（HKStockConfig等） | config/ | REQ-HK-025~027 | T09, HK-T02 | P0 | 1.5h |
| HK-T04 | 港股fetcher子模块目录与基类复用 | fetcher/hk/ | REQ-HK-001 | T10, T11 | P0 | 0.5h |
| HK-T05 | IFRS/HKFRS字段映射器FieldMapper | fetcher/hk/ | REQ-HK-004~005, NFR-HK-002, NFR-HK-003 | HK-T02, HK-T04 | P0 | 2h |
| HK-T06 | 港股通成分股获取器HKIndexFetcher | fetcher/hk/ | REQ-HK-001~003 | HK-T04 | P1 | 1.5h |
| HK-T07 | 港股财务数据获取器HKFinanceFetcher | fetcher/hk/ | REQ-HK-004~008, NFR-HK-005 | HK-T05 | P1 | 2.5h |
| HK-T08 | 港股市值数据获取器HKMarketFetcher | fetcher/hk/ | REQ-HK-009, REQ-HK-010 | HK-T04 | P1 | 1.5h |
| HK-T09 | 港股分红数据获取器HKDividendFetcher | fetcher/hk/ | REQ-HK-011~013 | HK-T04 | P1 | 1.5h |
| HK-T10 | 港币/人民币汇率转换器CurrencyConverter | fetcher/hk/ | REQ-HK-014, REQ-HK-015 | HK-T03, HK-T04 | P2 | 1h |
| HK-T11 | 港股退市风险过滤HKDelistingFilter | analyzer/ | REQ-HK-016~019 | T05, HK-T03 | P1 | 2h |
| HK-T12 | 配置文件config.yaml港股区块扩展 | config/ | REQ-HK-025, REQ-HK-026 | HK-T03 | P1 | 1h |
| HK-T13 | 输出层扩展（港股CSV/表格/格式化） | output/ | REQ-HK-022~024 | HK-T01, T22, T23 | P1 | 1.5h |
| HK-T14 | 主程序入口市场模式路由扩展 | 入口层 | REQ-HK-028~031 | HK-T03, HK-T06~T09, HK-T11, HK-T13 | P2 | 2h |
| HK-T15 | 港股单模块单元测试 | tests/ | REQ-HK-001~019 | HK-T06~T11 | P2 | 3h |
| HK-T16 | 港股集成测试与端到端验证 | tests/ | 全部REQ-HK, NFR-HK-001 | HK-T14 | P2 | 2h |

**港股通总计：16个任务，预估总工时约 23.5 小时**

---

## 港股通任务详细描述

---

### HK-T01: 数据模型扩展（market/currency字段）

- **任务名称**：数据模型扩展（market/currency字段）
- **所属模块**：common/models.py
- **关联需求**：REQ-HK-022, REQ-HK-014
- **前置任务**：T05
- **优先级**：P0
- **预估工时**：1h

- **任务描述**：
  扩展现有数据模型，为StockInfo和ScoredResult新增市场标识与货币字段，确保向后兼容。

  具体修改：
  - `StockInfo` 新增 `market: str = "A"` 字段，标识市场（"A"=A股, "HK"=港股）
  - `ScoredResult` 新增 `market: str = "A"` 字段
  - `ScoredResult` 新增 `currency: str = "CNY"` 字段（港股为"HKD"）
  - `ScoredResult` 新增 `deducted_net_profit_is_estimated: bool = False` 字段（扣非净利润是否为估算值）
  - 所有新字段均带默认值，确保现有A股代码中构造StockInfo/ScoredResult无需修改

- **验收标准**：
  - StockInfo新增market字段，默认值"A"
  - ScoredResult新增market、currency、deducted_net_profit_is_estimated字段，默认值分别为"A"、"CNY"、False
  - 现有A股代码中所有StockInfo/ScoredResult构造不报错，向后兼容
  - 运行现有A股单元测试全部通过

---

### HK-T02: 港股字段映射配置hk_field_mapping.yaml

- **任务名称**：港股字段映射配置hk_field_mapping.yaml
- **所属模块**：config/hk_field_mapping.yaml
- **关联需求**：NFR-HK-002, NFR-HK-003
- **前置任务**：T09
- **优先级**：P0
- **预估工时**：1h

- **任务描述**：
  创建港股IFRS/HKFRS财报字段到系统标准字段的映射配置文件，实现字段映射配置化（NFR-HK-002），使数据源字段名变更时仅需修改配置而非代码（NFR-HK-003）。

  具体内容：
  - 创建 `config/hk_field_mapping.yaml` 文件
  - 定义 `balance_sheet` 映射区块：cash_and_equivalents、total_current_assets、total_assets、total_current_liabilities、total_liabilities、net_assets的字段候选列表
  - 定义 `interest_bearing_debt_items` 列表：短期银行借款、长期银行借款、应付债券、融资租赁负债（中英文双语候选）
  - 定义 `income_statement` 映射区块：revenue、operating_cost、net_profit、deducted_net_profit
  - 定义 `cash_flow` 映射区块：operating_cash_flow、capital_expenditure
  - 每个标准字段映射为一组候选字段名（按优先级排列），支持中英文双语匹配

- **验收标准**：
  - `config/hk_field_mapping.yaml` 文件存在且YAML格式正确
  - 包含balance_sheet、income_statement、cash_flow、interest_bearing_debt_items四个区块
  - 每个映射字段至少包含中英文两种候选名称
  - YAML可被pyyaml正确加载为dict

---

### HK-T03: 港股配置类扩展（HKStockConfig等）

- **任务名称**：港股配置类扩展（HKStockConfig等）
- **所属模块**：config/settings.py
- **关联需求**：REQ-HK-025~027
- **前置任务**：T09, HK-T02
- **优先级**：P0
- **预估工时**：1.5h

- **任务描述**：
  在settings.py中新增港股专用配置数据类，并扩展Settings以支持market模式选择和hk_stock配置区块。

  具体新增：
  - `HKDataSourceConfig`：primary="akshare", fallback="eastmoney"
  - `HKConstituentsConfig`：include_sse=True, include_szse=True
  - `HKCurrencyConfig`：unit="HKD", convert_to_cny=False, fixed_hkd_cny_rate=0.0
  - `HKDelistingConfig`：max_suspend_months=3, min_market_cap_hkd=50000000.0, filter_audit_opinion=True
  - `HKStockConfig`：聚合以上子配置 + 可选的港股analyzer配置（asset_cushion/scoring）
  - `Settings` 扩展：新增 `market: str = "ALL"` 字段 + `hk_stock: HKStockConfig` 字段
  - 实现港股配置缺失时使用默认值逻辑（REQ-HK-027）
  - 新增 `hk_field_mapping_path` 配置项指向 `config/hk_field_mapping.yaml`

- **验收标准**：
  - 所有港股配置dataclass定义完成，带正确默认值
  - Settings新增market和hk_stock字段，market默认"ALL"
  - 配置文件中缺少hk_stock区块时，Settings加载不报错，使用默认值
  - 现有A股配置加载行为不变（向后兼容）

---

### HK-T04: 港股fetcher子模块目录与基类复用

- **任务名称**：港股fetcher子模块目录与基类复用
- **所属模块**：fetcher/hk/
- **关联需求**：REQ-HK-001
- **前置任务**：T10, T11
- **优先级**：P0
- **预估工时**：0.5h

- **任务描述**：
  创建港股数据获取子模块目录结构，复用现有BaseFetcher和DataCache。

  具体内容：
  - 创建 `fetcher/hk/` 目录
  - 创建 `fetcher/hk/__init__.py`，导出所有港股fetcher类
  - 确认BaseFetcher和DataCache可被港股fetcher子模块正常继承和使用
  - 确认港股fetcher返回的数据模型（StockFullData等）与A股一致，analyzer层无需修改

- **验收标准**：
  - `fetcher/hk/` 目录存在，`__init__.py` 可正常导入
  - `python -c "from fetcher.hk import ..."` 无报错
  - BaseFetcher和DataCache可被fetcher/hk/下模块正常引用

---

### HK-T05: IFRS/HKFRS字段映射器FieldMapper

- **任务名称**：IFRS/HKFRS字段映射器FieldMapper
- **所属模块**：fetcher/hk/field_mapper.py
- **关联需求**：REQ-HK-004, REQ-HK-005, NFR-HK-002, NFR-HK-003
- **前置任务**：HK-T02, HK-T04
- **优先级**：P0
- **预估工时**：2h

- **任务描述**：
  实现港股IFRS/HKFRS财报字段到系统标准字段的映射器，从hk_field_mapping.yaml加载映射关系，支持配置化字段映射。

  具体实现：
  - `FieldMapper.__init__(mapping_config)`：从YAML加载的dict初始化三类映射（balance/income/cashflow）和有息负债科目列表
  - `map_balance_sheet(raw_row)` → dict：映射港股资产负债表字段，特殊处理有息负债按科目逐项累加、应付债券缺失计0（REQ-HK-005）、净资产优先归属母公司股东权益
  - `map_income_statement(raw_row)` → tuple[dict, bool]：映射利润表字段，特殊处理扣非净利润缺失时用净利润替代并标记估算（REQ-HK-007）
  - `map_cash_flow(raw_row)` → dict：映射现金流量表字段，capital_expenditure匹配IFRS常用"Purchase of PPE"，free_cash_flow计算得出
  - `_calc_interest_bearing_debt(raw_row)` → float：按配置的有息负债科目列表逐项累加，缺失科目计0
  - 每个标准字段的候选字段名按优先级逐一匹配原始数据

- **验收标准**：
  - FieldMapper可从hk_field_mapping.yaml正确加载映射配置
  - 输入含英文字段名的港股原始数据，输出为系统标准字段名的dict
  - 输入含中文字段名的港股原始数据，输出同样正确
  - 有息负债按配置科目累加，缺失科目计0不报错
  - 扣非净利润缺失时使用净利润替代，返回估算标记为True

---

### HK-T06: 港股通成分股获取器HKIndexFetcher

- **任务名称**：港股通成分股获取器HKIndexFetcher
- **所属模块**：fetcher/hk/hk_index_fetcher.py
- **关联需求**：REQ-HK-001, REQ-HK-002, REQ-HK-003
- **前置任务**：HK-T04
- **优先级**：P1
- **预估工时**：1.5h

- **任务描述**：
  实现港股通（沪港通+深港通）成分股获取器，从akshare获取当前全部港股通标的股票。

  具体实现：
  - `HKIndexFetcher(BaseFetcher)` 继承基类
  - `fetch()` → list[StockInfo]：获取港股通全部标的，流程：获取沪港通标的→获取深港通标的→合并去重→记录日志
  - `_fetch_sse_constituents()`：调用 `ak.stock_hk_ggt_components_em(indicator="沪港通")` 获取沪港通标的，根据配置 `include_sse` 控制是否获取
  - `_fetch_szse_constituents()`：调用 `ak.stock_hk_ggt_components_em(indicator="深港通")` 获取深港通标的，根据配置 `include_szse` 控制是否获取
  - `_merge_and_deduplicate(sse_list, szse_list)`：以5位港股代码为唯一键合并去重
  - 返回的StockInfo中 `code` 为5位港股代码（如"00700"），`exchange="HK"`，`market="HK"`
  - 获取失败时记录错误日志并抛出DataFetchError，终止选股流程（REQ-HK-003）

- **验收标准**：
  - fetch()返回非空列表，所有StockInfo的market="HK"，exchange="HK"
  - 股票代码均为5位格式（不足5位前补零）
  - 沪港通和深港通标的已合并去重，无重复代码
  - 日志记录沪港通/深港通标的数量
  - akshare接口调用失败时抛出DataFetchError，不返回空列表

---

### HK-T07: 港股财务数据获取器HKFinanceFetcher

- **任务名称**：港股财务数据获取器HKFinanceFetcher
- **所属模块**：fetcher/hk/hk_finance_fetcher.py
- **关联需求**：REQ-HK-004~008, NFR-HK-005
- **前置任务**：HK-T05
- **优先级**：P1
- **预估工时**：2.5h

- **任务描述**：
  实现港股财务数据（资产负债表/利润表/现金流量表）获取器，通过FieldMapper进行IFRS/HKFRS字段映射，输出与A股FinanceFetcher统一的系统标准模型。

  具体实现：
  - `HKFinanceFetcher(BaseFetcher)` 继承基类，持有 `FieldMapper` 实例
  - `fetch_balance_sheet(stock_code)` → BalanceSheet：调用akshare港股财务报表接口 + FieldMapper.map_balance_sheet()，优先使用合并报表（NFR-HK-005）
  - `fetch_income_statement(stock_code)` → tuple[IncomeStatement, bool]：获取利润表 + FieldMapper.map_income_statement()，返回扣非净利润估算标记
  - `fetch_cash_flow(stock_code)` → CashFlowStatement：获取现金流量表 + FieldMapper.map_cash_flow()
  - `fetch_multi_year_deducted_profit(stock_code, years=3)` → list[float]：获取近N年扣非净利润，缺失时使用净利润替代
  - akshare接口：`ak.stock_hk_financial_report_em(symbol="00700", indicator="资产负债表/利润表/现金流量表")`
  - 数据获取失败时记录警告，返回None或默认值，不中断整体流程

- **验收标准**：
  - fetch_balance_sheet返回BalanceSheet实例，字段名与A股一致
  - fetch_income_statement返回(利润表, 是否估算)元组，扣非净利润缺失时估算标记为True
  - fetch_cash_flow返回CashFlowStatement实例，free_cash_flow由OCF-CAPEX计算得出
  - 有息负债含融资租赁负债科目（通过FieldMapper配置累加）
  - 合并报表优先于母公司报表
  - 单只股票数据获取失败不中断整体流程

---

### HK-T08: 港股市值数据获取器HKMarketFetcher

- **任务名称**：港股市值数据获取器HKMarketFetcher
- **所属模块**：fetcher/hk/hk_market_fetcher.py
- **关联需求**：REQ-HK-009, REQ-HK-010
- **前置任务**：HK-T04
- **优先级**：P1
- **预估工时**：1.5h

- **任务描述**：
  实现港股市值数据（总市值/流通市值/最新股价）批量获取器，市值单位为港币（HKD）。

  具体实现：
  - `HKMarketFetcher(BaseFetcher)` 继承基类
  - `fetch_batch_market_data(stock_codes)` → dict[str, MarketData]：批量获取港股市值数据
  - `_fetch_via_tencent_hk(stock_codes)`：优先使用腾讯行情港股接口（URL: `http://qt.gtimg.cn/q=hk00700,hk00941,...`），港股代码前缀为"hk"
  - `_fetch_via_akshare_hk()`：备选akshare `ak.stock_hk_spot_em()` 接口
  - 返回的MarketData中市值单位为港币，与A股的人民币区分
  - 市值数据缺失的股票标注并跳过，不中断整体流程（REQ-HK-010）

- **验收标准**：
  - fetch_batch_market_data返回dict，key为5位港股代码，value为MarketData
  - 市值单位为港币（HKD）
  - 腾讯行情港股接口返回数据可正确解析为MarketData
  - 某只股票市值数据缺失时不中断，跳过该股并记录警告日志
  - 优先使用腾讯行情接口，失败时回退到akshare接口

---

### HK-T09: 港股分红数据获取器HKDividendFetcher

- **任务名称**：港股分红数据获取器HKDividendFetcher
- **所属模块**：fetcher/hk/hk_dividend_fetcher.py
- **关联需求**：REQ-HK-011, REQ-HK-012, REQ-HK-013
- **前置任务**：HK-T04
- **优先级**：P1
- **预估工时**：1.5h

- **任务描述**：
  实现港股分红数据获取器，获取近3年分红数据，处理港股特有的"港仙(cent)→港元(HKD)"单位转换。

  具体实现：
  - `HKDividendFetcher(BaseFetcher)` 继承基类
  - `fetch_dividend_data(stock_code, latest_price=0.0)` → DividendData：获取近3年分红数据
  - `_convert_cent_to_hkd(value)` → float：港仙转港元，value/100（REQ-HK-012）
  - 单位判断逻辑：通过字段名或单位标识自动判断分红数据是"仙"还是"港元"，仙则除以100转换
  - 分红数据获取失败时返回默认值（0），记录警告日志，不中断流程（REQ-HK-013）
  - akshare接口：`ak.stock_hk_dividend_detail(symbol="00700")` 或类似接口

- **验收标准**：
  - fetch_dividend_data返回DividendData实例，金额单位为港元
  - 港仙单位数据自动除以100转换为港元
  - 近3年累计每股现金分红、股息率、分红年数计算正确
  - 分红数据获取失败时返回默认值(0)，不抛异常，记录警告

---

### HK-T10: 港币/人民币汇率转换器CurrencyConverter

- **任务名称**：港币/人民币汇率转换器CurrencyConverter
- **所属模块**：fetcher/hk/currency_converter.py
- **关联需求**：REQ-HK-014, REQ-HK-015
- **前置任务**：HK-T03, HK-T04
- **优先级**：P2
- **预估工时**：1h

- **任务描述**：
  实现港币/人民币汇率转换器，默认关闭汇率换算（各市场独立计价），仅当配置启用时进行换算。

  具体实现：
  - `CurrencyConverter.__init__(config: HKCurrencyConfig)`：持有汇率配置
  - `get_hkd_cny_rate()` → float：获取HKD/CNY汇率，优先使用配置固定汇率，其次akshare实时汇率接口
  - `convert_hkd_to_cny(amount_hkd)` → float：港元→人民币换算，仅当convert_to_cny=True时调用，否则原样返回
  - 默认convert_to_cny=False，港股结果以港币独立计价（REQ-HK-014）
  - 汇率获取失败时使用固定汇率或跳过换算，记录警告

- **验收标准**：
  - convert_to_cny=False时，convert_hkd_to_cny返回原值不做转换
  - convert_to_cny=True时，convert_hkd_to_cny正确乘以HKD/CNY汇率
  - 固定汇率>0时优先使用，不再调用实时接口
  - 汇率获取失败时记录警告，不抛异常

---

### HK-T11: 港股退市风险过滤HKDelistingFilter

- **任务名称**：港股退市风险过滤HKDelistingFilter
- **所属模块**：analyzer/hk_delisting_filter.py
- **关联需求**：REQ-HK-016~019
- **前置任务**：T05, HK-T03
- **优先级**：P1
- **预估工时**：2h

- **任务描述**：
  实现港交所退市风险过滤器，使用港交所退市规则替代A股ST标记制度。

  具体实现：
  - `HKDelistingFilter.__init__(config: HKDelistingConfig)`：持有退市配置
  - `is_delisting_risk(stock)` → bool：按以下顺序逐项检查：停牌时长→净资产为负→审计意见→最低市值→退市整理期
  - `filter(stocks)` → list[StockFullData]：批量过滤，返回保留的股票列表
  - `_check_suspend_duration(stock)` → bool：连续停牌超过max_suspend_months个月则剔除
  - `_check_negative_net_assets(stock)` → bool：归属母公司股东权益<0则剔除
  - `_check_audit_opinion(stock)` → bool：审计意见为"无法表示意见"或"否定意见"则剔除；缺少审计意见信息时保留，记录警告（REQ-HK-019）
  - `_check_min_market_cap(stock)` → bool：总市值<min_market_cap_hkd则剔除（默认5,000万港元）
  - `_check_delisting_period(stock)` → bool：处于退市整理期则剔除（REQ-HK-018），通过股票名称中"退市"标记判断
  - 不使用ST标记制度（与A股DelistingFilter的核心差异）

- **验收标准**：
  - 连续停牌超3个月股票被剔除
  - 净资产为负股票被剔除
  - 非标审计意见股票被剔除
  - 市值低于5,000万港元股票被剔除
  - 退市整理期股票被剔除
  - 无法判断退市风险的股票保留，记录警告
  - 不使用ST标记逻辑

---

### HK-T12: 配置文件config.yaml港股区块扩展

- **任务名称**：配置文件config.yaml港股区块扩展
- **所属模块**：config/default_config.yaml / config.yaml
- **关联需求**：REQ-HK-025, REQ-HK-026
- **前置任务**：HK-T03
- **优先级**：P1
- **预估工时**：1h

- **任务描述**：
  在config.yaml中新增market字段和hk_stock港股专用配置区块。

  具体新增：
  - 顶层新增 `market: "ALL"` 字段，取值"A"/"HK"/"ALL"
  - 新增 `hk_stock` 配置区块，包含：
    - `data_source`：primary="akshare", fallback="eastmoney"
    - `constituents`：include_sse=true, include_szse=true
    - `currency`：unit="HKD", convert_to_cny=false, fixed_hkd_cny_rate=0
    - `delisting`：max_suspend_months=3, min_market_cap_hkd=50000000, filter_audit_opinion=true
    - `asset_cushion`（可选）：港股专用资产垫阈值覆盖
    - `scoring`（可选）：港股专用评分权重覆盖
  - default_config.yaml同步新增对应区块和默认值

- **验收标准**：
  - config.yaml包含market字段和hk_stock区块
  - default_config.yaml包含相同的默认配置结构
  - Settings.load("config.yaml")可正确加载market和hk_stock配置
  - 缺少hk_stock区块时加载不报错，使用默认值

---

### HK-T13: 输出层扩展（港股CSV/表格/格式化）

- **任务名称**：输出层扩展（港股CSV/表格/格式化）
- **所属模块**：output/csv_writer.py, output/table_printer.py
- **关联需求**：REQ-HK-022, REQ-HK-023, REQ-HK-024
- **前置任务**：HK-T01, T22, T23
- **优先级**：P1
- **预估工时**：1.5h

- **任务描述**：
  扩展输出层以支持港股选股结果的独立输出，包括港股专属字段和独立CSV文件。

  具体修改：
  - `format_scored_result(r)` 扩展：新增"市场"、"货币"列；现金流列动态显示货币单位；港股附加"扣非净利润估算"列
  - `CsvWriter.write_hk(results)` → str：写入港股选股结果CSV，文件名格式 `hk_stock_selection_YYYYMMDD_HHMMSS.csv`
  - 港股与A股结果输出为独立文件，不合并（REQ-HK-024）
  - `TablePrinter` 扩展：支持港股专属列的终端表格展示

- **验收标准**：
  - 港股CSV文件名包含"hk"标识和日期，与A股文件名不冲突
  - CSV中包含"市场"="HK"、"货币"="HKD"列
  - 港股结果包含"扣非净利润估算"列
  - 现金流列标题动态显示货币单位（如"自由现金流(HKD)"）
  - A股输出格式不变（向后兼容）
  - A股和港股结果输出为独立文件

---

### HK-T14: 主程序入口市场模式路由扩展

- **任务名称**：主程序入口市场模式路由扩展
- **所属模块**：main.py
- **关联需求**：REQ-HK-028, REQ-HK-029, REQ-HK-030, REQ-HK-031
- **前置任务**：HK-T03, HK-T06, HK-T07, HK-T08, HK-T09, HK-T11, HK-T13
- **优先级**：P2
- **预估工时**：2h

- **任务描述**：
  扩展main.py支持market模式路由，根据配置中的market值（"A"/"HK"/"ALL"）选择执行A股选股、港股通选股或两者依次执行。

  具体修改：
  - `main()` 扩展：读取 `settings.market`，按值路由到对应选股流程
  - `run_a_stock_selection(settings, logger)` → list[ScoredResult]：A股选股流程，与原main()逻辑完全一致，向后兼容（REQ-HK-030）
  - `run_hk_stock_selection(settings, logger)` → list[ScoredResult]：港股通选股完整流程：
    1. 港股通成分股获取（HKIndexFetcher）
    2. 港股市值数据批量获取（HKMarketFetcher）
    3. 港股财务数据逐只获取（HKFinanceFetcher + FieldMapper）
    4. 港股分红数据逐只获取（HKDividendFetcher，仙→港元转换）
    5. 港股退市风险过滤（HKDelistingFilter，港交所规则）
    6. 核心筛选与评分（复用A股analyzer：AssetCushion/OperationSafety/RedemptionSafety/Scorer，使用港股专用配置）
    7. 港股结果输出（独立CSV + 表格）
  - market="ALL"时依次执行A股和港股流程，分别记录日志（REQ-HK-029）
  - 启动时输出市场模式标识（"A股模式"/"港股通模式"/"全市场模式"）（REQ-HK-031）
  - `_get_hk_asset_cushion_config(settings)`：港股配置覆盖机制，优先使用港股专用配置，未定义时回退到A股默认（REQ-HK-021）

- **验收标准**：
  - market="A"时仅执行A股选股，行为与扩展前完全一致
  - market="HK"时执行港股通完整选股流程
  - market="ALL"时依次执行A股和港股选股，分别输出独立结果文件
  - 启动日志输出当前市场模式标识
  - 港股选股复用A股analyzer层，使用港股专用配置覆盖
  - 港股选股流程异常不导致A股流程受影响（ALL模式下隔离）

---

### HK-T15: 港股单模块单元测试

- **任务名称**：港股单模块单元测试
- **所属模块**：tests/
- **关联需求**：REQ-HK-001~019
- **前置任务**：HK-T06, HK-T07, HK-T08, HK-T09, HK-T10, HK-T11
- **优先级**：P2
- **预估工时**：3h

- **任务描述**：
  为港股新增模块编写单元测试，覆盖核心逻辑和边界条件。

  具体测试：
  - `test_field_mapper.py`：测试FieldMapper字段映射（中英文候选匹配、有息负债累加、扣非净利润缺失替代、应付债券缺失计0）
  - `test_hk_index_fetcher.py`：测试HKIndexFetcher（合并去重、5位代码格式、获取失败抛异常）
  - `test_hk_finance_fetcher.py`：测试HKFinanceFetcher（三表映射、估算标记、多年净利缺失处理）
  - `test_hk_market_fetcher.py`：测试HKMarketFetcher（批量获取、缺失跳过、港币单位）
  - `test_hk_dividend_fetcher.py`：测试HKDividendFetcher（仙→港元转换、缺失默认值0）
  - `test_hk_delisting_filter.py`：测试HKDelistingFilter（五项过滤规则、无法判断保留、不使用ST）
  - `test_currency_converter.py`：测试CurrencyConverter（关闭换算、开启换算、固定汇率、获取失败降级）
  - 使用mock模拟akshare接口返回数据

- **验收标准**：
  - 所有单元测试通过
  - FieldMapper字段映射测试覆盖中英文候选
  - HKDelistingFilter测试覆盖五项过滤规则和边界条件
  - 分红数据仙→港元转换测试正确
  - 扣非净利润估算标记逻辑测试正确

---

### HK-T16: 港股集成测试与端到端验证

- **任务名称**：港股集成测试与端到端验证
- **所属模块**：tests/
- **关联需求**：全部REQ-HK, NFR-HK-001
- **前置任务**：HK-T14
- **优先级**：P2
- **预估工时**：2h

- **任务描述**：
  执行港股通选股功能的集成测试和端到端验证，确保完整流程可用。

  具体测试：
  - **港股单次完整流程测试**：market="HK"模式下运行完整选股流程，验证输出结果文件存在且格式正确
  - **A股模式向后兼容测试**：market="A"模式下运行，验证行为与扩展前完全一致
  - **全市场模式测试**：market="ALL"模式下运行，验证A股和港股结果分别独立输出
  - **性能测试**：验证港股单次完整选股流程在8分钟内完成（NFR-HK-001）
  - **配置缺失降级测试**：删除hk_stock区块后运行，验证使用默认值不报错
  - **数据源异常测试**：模拟akshare接口异常，验证错误处理和日志记录
  - **结果文件验证**：检查港股CSV文件包含所有必备列（市场/货币/扣非净利润估算）

- **验收标准**：
  - market="HK"模式下完整选股流程可正常运行并输出结果
  - market="A"模式下行为与扩展前一致，现有A股测试全部通过
  - market="ALL"模式下A股和港股结果分别输出为独立文件
  - 港股选股流程在8分钟内完成
  - 配置缺失时使用默认值，不报错
  - 数据源异常时有正确的错误处理和日志

---

## 港股通任务依赖关系图

```
HK-T01 (数据模型扩展)
HK-T02 (字段映射配置) ──→ HK-T05 (FieldMapper) ──→ HK-T07 (HKFinanceFetcher)
HK-T03 (港股配置类)  ──┬── HK-T10 (CurrencyConverter)
                        ├── HK-T11 (HKDelistingFilter) ──┐
                        └── HK-T12 (config.yaml扩展)    ──┤
HK-T04 (fetcher/hk目录) ──┬── HK-T05 (FieldMapper)       │
                           ├── HK-T06 (HKIndexFetcher)    │
                           ├── HK-T08 (HKMarketFetcher)   │
                           └── HK-T09 (HKDividendFetcher) │
HK-T01 ──→ HK-T13 (输出层扩展)                             │
HK-T06~T09, HK-T11, HK-T13 ──→ HK-T14 (main.py路由扩展) ──→ HK-T16 (集成测试)
HK-T06~T11 ──→ HK-T15 (单元测试)
```

---

## 港股通需求覆盖追溯矩阵

| 需求编号 | 需求描述 | 覆盖任务 |
|----------|----------|----------|
| REQ-HK-001 | 港股通成分股获取 | HK-T06 |
| REQ-HK-002 | 沪港通+深港通合并去重 | HK-T06 |
| REQ-HK-003 | 成分股获取失败终止 | HK-T06 |
| REQ-HK-004 | 港股资产负债表映射 | HK-T05, HK-T07 |
| REQ-HK-005 | 港股有息负债计算 | HK-T05 |
| REQ-HK-006 | 港股利润表映射 | HK-T05, HK-T07 |
| REQ-HK-007 | 扣非净利润缺失处理 | HK-T05, HK-T07 |
| REQ-HK-008 | 港股现金流量表映射 | HK-T05, HK-T07 |
| REQ-HK-009 | 港股市值数据获取 | HK-T08 |
| REQ-HK-010 | 市值数据缺失跳过 | HK-T08 |
| REQ-HK-011 | 港股分红数据获取 | HK-T09 |
| REQ-HK-012 | 仙→港元单位转换 | HK-T09 |
| REQ-HK-013 | 分红数据缺失默认值 | HK-T09 |
| REQ-HK-014 | 港币独立计价输出 | HK-T01, HK-T10, HK-T13 |
| REQ-HK-015 | 汇率统一换算(可选) | HK-T10 |
| REQ-HK-016 | 港股退市风险过滤 | HK-T11 |
| REQ-HK-017 | 港交所退市规则 | HK-T11 |
| REQ-HK-018 | 退市整理期过滤 | HK-T11 |
| REQ-HK-019 | 无法判断时保留 | HK-T11 |
| REQ-HK-020 | 核心筛选逻辑复用 | HK-T14 |
| REQ-HK-021 | 港股专用阈值覆盖 | HK-T03, HK-T14 |
| REQ-HK-022 | 港股结果输出格式 | HK-T01, HK-T13 |
| REQ-HK-023 | 港股独立CSV文件 | HK-T13 |
| REQ-HK-024 | A股/港股独立输出 | HK-T13, HK-T14 |
| REQ-HK-025 | market配置字段 | HK-T03, HK-T12 |
| REQ-HK-026 | hk_stock配置区块 | HK-T03, HK-T12 |
| REQ-HK-027 | 港股配置默认值 | HK-T03 |
| REQ-HK-028 | 港股选股流程初始化 | HK-T14 |
| REQ-HK-029 | ALL模式依次执行 | HK-T14 |
| REQ-HK-030 | A模式向后兼容 | HK-T14 |
| REQ-HK-031 | 启动输出市场标识 | HK-T14 |
| NFR-HK-001 | 8分钟完成 | HK-T16 |
| NFR-HK-002 | 字段映射配置化 | HK-T02, HK-T05 |
| NFR-HK-003 | 字段名变更快速适配 | HK-T02, HK-T05 |
| NFR-HK-004 | analyzer层代码共享 | HK-T14 |
| NFR-HK-005 | 优先合并报表 | HK-T07 |
