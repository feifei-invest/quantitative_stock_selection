import logging
import os
from datetime import datetime


class LoggerManager:
    _initialized = False

    @staticmethod
    def setup(log_dir: str = "logs", log_level: str = "INFO") -> logging.Logger:
        if LoggerManager._initialized:
            return logging.getLogger("stock_selection")

        os.makedirs(log_dir, exist_ok=True)

        logger = logging.getLogger("stock_selection")
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        date_str = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"stock_selection_{date_str}.log")

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        LoggerManager._initialized = True
        return logger
