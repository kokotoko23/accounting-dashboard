"""
取引先分析タブ - 取引先ランキングと業種別分析
"""

from typing import List, Optional, Callable

import customtkinter as ctk
from tkinter import ttk

from app.models.database import AccountingDatabase
from app.utils.chart_base import PieChartFrame, LineChartFrame


class CustomerRankingTable(ctk.CTkFrame):
    """取引先ランキングテーブル"""

    def __init__(
        self,
        parent,
        on_select: Optional[Callable[[str, str], None]] = None,
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
            text="取引先ランキング TOP20",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header.pack(pady=(10, 5), anchor="w", padx=10)

        # Treeview作成
        columns = ("rank", "customer", "industry", "amount")
        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=15
        )

        # 列の設定
        self.tree.heading("rank", text="順位")
        self.tree.heading("customer", text="取引先名")
        self.tree.heading("industry", text="業種")
        self.tree.heading("amount", text="金額")

        self.tree.column("rank", width=50, anchor="center")
        self.tree.column("customer", width=200)
        self.tree.column("industry", width=100)
        self.tree.column("amount", width=120, anchor="e")

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
            if len(values) >= 2:
                customer_name = values[1]
                industry = values[2]
                self.on_select(customer_name, industry)

    def update_data(self, data: list):
        """
        データを更新

        Args:
            data: [(順位, 取引先名, 業種, 金額), ...] のリスト
        """
        # 既存データをクリア
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 新しいデータを挿入
        for row in data:
            self.tree.insert("", "end", values=row)


class CustomerTab(ctk.CTkFrame):
    """取引先分析タブコンポーネント"""

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
        self.current_account: str = "売上高"

        # レイアウト設定
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_widgets()

    def _create_widgets(self):
        """ウィジェットを作成"""
        # 左上: 取引先ランキングテーブル
        self.ranking_table = CustomerRankingTable(
            self,
            on_select=self._on_customer_select
        )
        self.ranking_table.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)

        # 右上: 業種別構成比グラフ
        self.industry_chart = PieChartFrame(
            self,
            figsize=(5, 3.5),
            dpi=100
        )
        self.industry_chart.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # 右下: 選択取引先の月次推移
        self.customer_trend_chart = LineChartFrame(
            self,
            figsize=(5, 3.5),
            dpi=100
        )
        self.customer_trend_chart.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # 初期メッセージ
        self.customer_trend_chart.ax.text(
            0.5, 0.5, "取引先を選択してください",
            ha="center", va="center", fontsize=12
        )
        self.customer_trend_chart.redraw()

    def update_data(
        self,
        years: List[int],
        segments: List[str],
        account: str
    ):
        """
        データを更新

        Args:
            years: 選択された年度リスト
            segments: 選択されたセグメントリスト
            account: 選択された科目
        """
        self.current_years = years
        self.current_account = account

        if not years:
            return

        # 最新年度のデータを使用
        latest_year = max(years)

        # 取引先ランキングを更新
        self._update_ranking(latest_year, account)

        # 業種別構成比を更新
        self._update_industry_chart(latest_year, account)

    def _update_ranking(self, year: int, account: str):
        """取引先ランキングを更新"""
        df = self.db.get_customer_ranking(year, account, limit=20)

        if df.empty:
            self.ranking_table.update_data([])
            return

        # テーブルデータを作成
        data = []
        for i, row in df.iterrows():
            rank = i + 1
            customer = row["customer_name"]
            industry = row["industry"]
            amount = f"¥{int(row['total']):,}"
            data.append((rank, customer, industry, amount))

        self.ranking_table.update_data(data)

    def _update_industry_chart(self, year: int, account: str):
        """業種別構成比グラフを更新"""
        df = self.db.get_industry_summary(year, account)

        if df.empty:
            self.industry_chart.clear()
            self.industry_chart.set_title("業種別構成比（データなし）")
            self.industry_chart.redraw()
            return

        self.industry_chart.plot(
            labels=df["industry"].tolist(),
            values=df["total"].tolist(),
            title=f"業種別構成比 {year}年度 - {account}"
        )

    def _on_customer_select(self, customer_name: str, industry: str):
        """取引先選択時の処理"""
        if not self.current_years:
            return

        self._update_customer_trend(customer_name)

    def _update_customer_trend(self, customer_name: str):
        """選択取引先の月次推移を更新"""
        if not self.current_years:
            return

        conn = self.db.connection
        account = self.current_account

        # 年度ごとの月次データを取得
        months = list(range(1, 13))
        y_data_dict = {}

        for year in sorted(self.current_years):
            placeholders = ",".join("?" * 12)
            query = f"""
                SELECT month, SUM(amount) as total
                FROM transactions_denormalized
                WHERE customer_name = ?
                  AND account = ?
                  AND year = ?
                  AND month IN ({placeholders})
                GROUP BY month
                ORDER BY month
            """
            params = [customer_name, account, year] + months

            cursor = conn.execute(query, params)
            results = {row[0]: row[1] for row in cursor.fetchall()}

            monthly_values = [results.get(m, 0) / 1_000_000 for m in months]
            y_data_dict[f"{year}年度"] = monthly_values

        if not y_data_dict:
            self.customer_trend_chart.clear()
            self.customer_trend_chart.set_title("データなし")
            self.customer_trend_chart.redraw()
            return

        self.customer_trend_chart.plot(
            x_data=months,
            y_data_dict=y_data_dict,
            xlabel="月",
            ylabel="金額（百万円）",
            title=f"{customer_name} - {account}"
        )

    def destroy(self):
        """リソースを解放"""
        if self._owns_db and self.db:
            self.db.close()
        super().destroy()
