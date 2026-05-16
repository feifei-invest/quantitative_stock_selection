import logging

from rich.console import Console
from rich.table import Table

from common.models import ScoredResult
from output.csv_writer import format_scored_result

logger = logging.getLogger(__name__)


class TablePrinter:
    def __init__(self, max_rows: int = 50):
        self.max_rows = max_rows
        self.console = Console()

    def print(self, results: list[ScoredResult]):
        if not results:
            self.console.print("[yellow]无符合条件的股票[/yellow]")
            return

        display = results[: self.max_rows]

        table = Table(title="沪深300价值股票选股结果", show_lines=True)
        table.add_column("排名", justify="right", style="cyan")
        table.add_column("代码", style="green")
        table.add_column("名称", style="white")
        table.add_column("资产垫等级", style="bold")
        table.add_column("保守比率", justify="right")
        table.add_column("宽松比率", justify="right")
        table.add_column("FCF(亿)", justify="right")
        table.add_column("资本开支率", justify="right")
        table.add_column("兑现路径", style="magenta")
        table.add_column("综合评分", justify="right", style="bold yellow")

        for r in display:
            tier_style = {"T0": "bold red", "T1": "bold green", "T2": "yellow", "FAIL": "dim"}.get(r.asset_cushion_tier, "")
            fcf_yi = r.free_cash_flow / 1e8
            capex_str = f"{r.capex_ratio:.2f}" if r.capex_ratio != float("inf") else "N/A"

            table.add_row(
                str(r.rank),
                r.stock_code,
                r.stock_name,
                f"[{tier_style}]{r.asset_cushion_tier}[/{tier_style}]" if tier_style else r.asset_cushion_tier,
                f"{r.conservative_ratio:.4f}",
                f"{r.loose_ratio:.4f}",
                f"{fcf_yi:.2f}",
                capex_str,
                r.redemption_path_type,
                f"{r.total_score:.1f}",
            )

        self.console.print(table)
        if len(results) > self.max_rows:
            self.console.print(f"[dim]仅显示前{self.max_rows}条, 共{len(results)}条结果[/dim]")
