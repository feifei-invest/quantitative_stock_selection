class StockSelectionError(Exception):
    pass


class DataFetchError(StockSelectionError):
    def __init__(self, stock_code: str = "", data_type: str = "", message: str = ""):
        self.stock_code = stock_code
        self.data_type = data_type
        self.message = message
        super().__init__(self._build_str())

    def _build_str(self) -> str:
        parts = []
        if self.stock_code:
            parts.append(f"股票={self.stock_code}")
        if self.data_type:
            parts.append(f"数据类型={self.data_type}")
        if self.message:
            parts.append(self.message)
        return f"[DataFetchError] {', '.join(parts)}" if parts else "[DataFetchError]"

    def __str__(self) -> str:
        return self._build_str()


class DataMissingError(StockSelectionError):
    def __init__(self, stock_code: str = "", missing_fields: list = None, message: str = ""):
        self.stock_code = stock_code
        self.missing_fields = missing_fields or []
        self.message = message
        super().__init__(self._build_str())

    def _build_str(self) -> str:
        parts = []
        if self.stock_code:
            parts.append(f"股票={self.stock_code}")
        if self.missing_fields:
            parts.append(f"缺失字段={self.missing_fields}")
        if self.message:
            parts.append(self.message)
        return f"[DataMissingError] {', '.join(parts)}" if parts else "[DataMissingError]"

    def __str__(self) -> str:
        return self._build_str()


class DataValidationError(StockSelectionError):
    def __init__(self, stock_code: str = "", message: str = ""):
        self.stock_code = stock_code
        self.message = message
        super().__init__(self._build_str())

    def _build_str(self) -> str:
        parts = []
        if self.stock_code:
            parts.append(f"股票={self.stock_code}")
        if self.message:
            parts.append(self.message)
        return f"[DataValidationError] {', '.join(parts)}" if parts else "[DataValidationError]"

    def __str__(self) -> str:
        return self._build_str()


class ConfigError(StockSelectionError):
    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(f"[ConfigError] {message}" if message else "[ConfigError]")

    def __str__(self) -> str:
        return f"[ConfigError] {self.message}" if self.message else "[ConfigError]"


class RateLimitError(DataFetchError):
    def __init__(self, stock_code: str = "", data_type: str = "", message: str = "API限流"):
        super().__init__(stock_code=stock_code, data_type=data_type, message=message)
