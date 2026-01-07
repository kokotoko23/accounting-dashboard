"""
事業部分析タブ - 事業部別の売上・利益分析
"""

from typing import List, Optional, Callable

import customtkinter as ctk
from tkinter import ttk

from app.models.database import AccountingDatabase
from app.utils.chart_base import BarChartFrame, LineChartFrame, PieChartFrame


class DivisionComparisonTable(ctk.CTkFrame):
    """事業部比較テーブル"""

    def __init__(
        self,
        parent,
        on_select: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.on_select = on_select

        # Treeviewのスタイル設定
        style = ttk.Style()
        style.configure("Treeview", rowheight=25, font=("", 11))
        style.configure("Treeview.Heading", font=("", 11, "bold"))

        # ヘッダーラベル
        header = ctk.CTkLabel(
            self,
            text="事業部別 売上・利益",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header.pack(pady=(10, 5), anchor="w", padx=10)

        # Treeview作成
        columns = ("division", "sales", "cost", "profit", "margin")
        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=10
        )

        # 列の設定
        self.tree.heading("division", text="事業部")
        self.tree.heading("sales", text="売上高")
        self.tree.heading("cost", text="売上原価")
        self.tree.heading("profit", text="売上総利益")
        self.tree.heading("margin", text="利益率")

        self.tree.column("division", width=120)
        self.tree.column("sales", width=100, anchor="e")
        self.tree.column("cost", width=100, anchor="e")
        self.tree.column("profit", width=100, anchor="e")
        self.tree.column("margin", width=70, anchor="center")

        # スクロールバー
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=5)
        scrollbar.pack(side="right", fill="y", pady=5, padx=(0, 10))

        # 選択イベント
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _on_tree_select(self, event):
        """行選択時の処理"""
        selection = self.tree.selection()
        if selection and self.on_select:
            item = self.tree.item(selection[0])
            values = item["values"]
            if values:
                division_name = values[0]
                self.on_select(division_name)

    def update_data(self, data: list):
        """
        データを更新

        Args:
            data: [(事業部, 売上高, 売上原価, 売上総利益, 利益率), ...] のリスト
        """
        # 既存データをクリア
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 新しいデータを挿入
        for row in data:
            self.tree.insert("", "end", values=row)


class DivisionTab(ctk.CTkFrame):
    """事業部分析タブコンポーネント"""

    def __init__(
        self,
        parent,
        db: Optional[AccountingDatabase] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.db = db if db else AccountingDatabase()
        self._owns_db = db is None

        # 現在のフィルタ値を保持
        self.current_years: List[int] = []
        self.current_divisions: List[str] = []
        self.current_account: str = "売上高"
        self.selected_division: Optional[str] = None

        # レイアウト設定
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_widgets()

    def _create_widgets(self):
        """ウィジェットを作成"""
        # 左上: 事業部比較テーブル
        self.comparison_table = DivisionComparisonTable(
            self,
            on_select=self._on_division_select
        )
        self.comparison_table.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # 右上: 事業部別売上構成比（円グラフ）
        self.share_chart = PieChartFrame(
            self,
            figsize=(5, 3.5),
            dpi=100
        )
        self.share_chart.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # 左下: 事業部別比較（棒グラフ - 売上と利益を並べて表示）
        self.comparison_chart = BarChartFrame(
            self,
            figsize=(5, 3.5),
            dpi=100
        )
        self.comparison_chart.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # 右下: 選択事業部の月次推移（売上・利益）
        self.trend_chart = LineChartFrame(
            self,
            figsize=(5, 3.5),
            dpi=100
        )
        self.trend_chart.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # 初期メッセージ
        self.trend_chart.ax.text(
            0.5, 0.5, "事業部を選択してください",
            ha="center", va="center", fontsize=12
        )
        self.trend_chart.redraw()

    def update_data(
        self,
        years: List[int],
        divisions: List[str],
        account: str
    ):
        """
        データを更新

        Args:
            years: 選択された年度リスト
            divisions: 選択された事業部リスト
            account: 選択された科目
        """
        self.current_years = years
        self.current_divisions = divisions
        self.current_account = account

        if not years:
            return

        # 事業部比較テーブルを更新（売上・利益表示）
        self._update_comparison_table(years)

        # 事業部別構成比グラフを更新
        self._update_share_chart(years, account)

        # 事業部別売上・利益比較グラフを更新
        self._update_profit_comparison_chart(years)

        # 選択事業部があれば月次推移も更新
        if self.selected_division:
            self._update_trend_chart(self.selected_division)

    def _update_comparison_table(self, years: List[int]):
        """事業部比較テーブルを更新（売上・利益表示）"""
        if not years:
            self.comparison_table.update_data([])
            return

        # 最新年度のデータを取得
        latest_year = max(years)
        df = self.db.get_division_profit_summary([latest_year])

        if df.empty:
            self.comparison_table.update_data([])
            return

        # テーブルデータを作成
        data = []
        for _, row in df.iterrows():
            division = row["division"]
            sales = row["sales"]
            cost = row["cost"]
            profit = row["profit"]

            # 利益率を計算
            if sales > 0:
                margin = f"{(profit / sales) * 100:.1f}%"
            else:
                margin = "-"

            data.append((
                division,
                f"¥{int(sales):,}",
                f"¥{int(cost):,}",
                f"¥{int(profit):,}",
                margin
            ))

        self.comparison_table.update_data(data)

    def _update_share_chart(self, years: List[int], account: str):
        """事業部別構成比グラフを更新"""
        if not years:
            self.share_chart.clear()
            self.share_chart.set_title("事業部構成比（データなし）")
            self.share_chart.redraw()
            return

        latest_year = max(years)
        df = self.db.get_division_summary([latest_year], account)

        if df.empty:
            self.share_chart.clear()
            self.share_chart.set_title("事業部構成比（データなし）")
            self.share_chart.redraw()
            return

        self.share_chart.plot(
            labels=df["division"].tolist(),
            values=df["total"].tolist(),
            title=f"事業部構成比 {latest_year}年度 - {account}"
        )

    def _update_profit_comparison_chart(self, years: List[int]):
        """事業部別売上・利益比較グラフを更新"""
        if not years:
            self.comparison_chart.clear()
            self.comparison_chart.set_title("事業部比較（年度を選択してください）")
            self.comparison_chart.redraw()
            return

        latest_year = max(years)
        df = self.db.get_division_profit_summary([latest_year])

        if df.empty:
            self.comparison_chart.clear()
            self.comparison_chart.set_title("事業部比較（データなし）")
            self.comparison_chart.redraw()
            return

        # 売上と利益を並べたグループ棒グラフを描画
        self._plot_grouped_bar(
            df["division"].tolist(),
            {
                "売上高": [v / 1_000_000 for v in df["sales"].tolist()],
                "売上総利益": [v / 1_000_000 for v in df["profit"].tolist()]
            },
            f"事業部別 売上・利益 {latest_year}年度"
        )

    def _plot_grouped_bar(self, labels: List[str], data_dict: dict, title: str):
        """グループ化された棒グラフを描画"""
        import numpy as np

        self.comparison_chart.clear()
        ax = self.comparison_chart.ax

        n_groups = len(labels)
        n_bars = len(data_dict)

        # 棒の幅を動的に計算
        total_width = 0.8
        width = total_width / n_bars

        x = np.arange(n_groups)

        # カラーパレット
        colors = ["#1976D2", "#4CAF50"]  # 青（売上）、緑（利益）

        for i, (label, values) in enumerate(data_dict.items()):
            offset = (i - n_bars / 2 + 0.5) * width
            ax.bar(x + offset, values, width, label=label, color=colors[i % len(colors)])

        ax.set_xlabel("事業部")
        ax.set_ylabel("金額（百万円）")
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.legend(loc="upper right")
        ax.grid(axis="y", alpha=0.3)

        self.comparison_chart.figure.tight_layout()
        self.comparison_chart.redraw()

    def _on_division_select(self, division_name: str):
        """事業部選択時の処理"""
        self.selected_division = division_name
        self._update_trend_chart(division_name)

    def _update_trend_chart(self, division_name: str):
        """選択事業部の月次推移を更新（売上・利益両方表示）"""
        if not self.current_years:
            return

        # 最新年度の月次データを取得
        latest_year = max(self.current_years)
        df = self.db.get_division_monthly_profit([latest_year], [division_name])

        if df.empty:
            self.trend_chart.clear()
            self.trend_chart.set_title("データなし")
            self.trend_chart.redraw()
            return

        months = list(range(1, 13))
        y_data_dict = {}

        # 売上高データ
        sales_values = []
        profit_values = []

        for month in months:
            month_data = df[df["month"] == month]
            if not month_data.empty:
                sales_values.append(month_data["sales"].values[0] / 1_000_000)
                profit_values.append(month_data["profit"].values[0] / 1_000_000)
            else:
                sales_values.append(0)
                profit_values.append(0)

        y_data_dict["売上高"] = sales_values
        y_data_dict["売上総利益"] = profit_values

        self.trend_chart.plot(
            x_data=months,
            y_data_dict=y_data_dict,
            xlabel="月",
            ylabel="金額（百万円）",
            title=f"{division_name} - 売上・利益推移 {latest_year}年度"
        )

    def destroy(self):
        """リソースを解放"""
        if self._owns_db and self.db:
            self.db.close()
        super().destroy()
