import logging
import os
from datetime import datetime

from common.models import ScoredResult

logger = logging.getLogger(__name__)


def format_scored_result(r: ScoredResult) -> dict:
    return {
        "排名": r.rank,
        "股票代码": r.stock_code,
        "股票名称": r.stock_name,
        "资产垫等级": r.asset_cushion_tier,
        "保守资产垫比率": f"{r.conservative_ratio:.4f}",
        "宽松资产垫比率": f"{r.loose_ratio:.4f}",
        "自由现金流(元)": f"{r.free_cash_flow:,.0f}",
        "资本开支率": f"{r.capex_ratio:.4f}" if r.capex_ratio != float("inf") else "N/A",
        "兑现路径": r.redemption_path_type,
        "资产垫得分": f"{r.asset_cushion_score:.0f}",
        "经营安全得分": f"{r.operation_safety_score:.0f}",
        "兑现安全得分": f"{r.redemption_safety_score:.0f}",
        "综合评分": f"{r.total_score:.2f}",
    }


class CsvWriter:
    def __init__(self, csv_dir: str = "output_data/results", encoding: str = "utf-8-sig"):
        self.csv_dir = csv_dir
        self.encoding = encoding
        os.makedirs(csv_dir, exist_ok=True)

    def write(self, results: list[ScoredResult]) -> str:
        if not results:
            logger.warning("无结果数据, 跳过CSV输出")
            return ""

        import csv

        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.csv_dir, f"stock_selection_{date_str}.csv")

        rows = [format_scored_result(r) for r in results]
        headers = list(rows[0].keys())

        with open(filepath, "w", newline="", encoding=self.encoding) as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        logger.info(f"CSV结果已写入: {filepath}")
        return filepath
