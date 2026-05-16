import logging
import requests

logger = logging.getLogger(__name__)


class CurrencyConverter:
    _rate: float = 0.0

    @classmethod
    def get_hkd_cny_rate(cls, fixed_rate: float = 0.0) -> float:
        if cls._rate > 0:
            return cls._rate
        if fixed_rate > 0:
            cls._rate = fixed_rate
            return cls._rate
        try:
            url = "http://qt.gtimg.cn/q=USDCNY"
            resp = requests.get(url, timeout=10)
            text = resp.text.strip()
            for line in text.split(";"):
                if '="' in line:
                    fields = line.split('="')[1].rstrip('"').split("~")
                    if len(fields) > 3:
                        cls._rate = float(fields[3])
                        logger.info(f"获取实时汇率 USD/CNY={cls._rate}")
                        break
            if cls._rate <= 0:
                cls._rate = 7.25
        except Exception:
            cls._rate = 7.25

        hkd_to_cny = cls._rate / 7.8
        logger.info(f"汇率 HKD/CNY={hkd_to_cny:.4f}")
        return hkd_to_cny

    @classmethod
    def convert_hkd_to_cny(cls, amount_hkd: float, rate: float = 0.0) -> float:
        if rate <= 0:
            rate = cls.get_hkd_cny_rate()
        return amount_hkd * rate

    @classmethod
    def reset(cls):
        cls._rate = 0.0
