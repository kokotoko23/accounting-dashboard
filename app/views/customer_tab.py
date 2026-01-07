"""
取引先分析タブ - 取引先ランキングと業種別分析
フィルタ: 年度（複数選択）、事業部（単一選択）
"""

from typing import Callable, Dict, List, Optional

import customtkinter as ctk
from tkinter import ttk

from app.models.database import AccountingDatabase
from app.utils.chart_base import PieChartFrame, LineChartFrame


class CustomerFilterPanel(ctk.CTkFrame):
    """取引先分析用フィルタパネル"""

    def __init__(
        self,
        parent,
        db: AccountingDatabase,
        on_filter_change: Callable,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.db = db
        self.on_filter_change = on_filter_change

        # フィルタ用変数
        self.year_vars: Dict[int, ctk.BooleanVar] = {}
        self.division_var = ctk.StringVar()

        self._create_widgets()

    def _create_widgets(self):
        """ウィジェットを作成"""
        # 横並びレイアウト
        self.grid_columnconfigure((0, 1), weight=1)

        # 年度フィルタ
        self._create_year_filter()

        # 事業部フィルタ（単一選択）
        self._create_division_filter()

        # フィルタ状況表示
        self._create_filter_status()

    def _create_year_filter(self):
        """年度フィルタを作成"""
        year_frame = ctk.CTkFrame(self)
        year_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        ctk.CTkLabel(
            year_frame, text="年度", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=5, pady=(5, 2))

        years = self.db.get_years()
        checkbox_frame = ctk.CTkFrame(year_frame, fg_color="transparent")
        checkbox_frame.pack(fill="x", padx=5)

        for year in years:
            var = ctk.BooleanVar(value=True)
            self.year_vars[year] = var
            cb = ctk.CTkCheckBox(
                checkbox_frame,
                text=f"{year}年",
                variable=var,
                command=self._on_change,
                width=80
            )
            cb.pack(side="left", padx=2)

    def _create_division_filter(self):
        """事業部フィルタを作成（単一選択ドロップダウン）"""
        div_frame = ctk.CTkFrame(self)
        div_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        ctk.CTkLabel(
            div_frame, text="事業部", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=5, pady=(5, 2))

        divisions = self.db.get_divisions()
        self.division_var.set(divisions[0] if divisions else "")

        self.division_dropdown = ctk.CTkOptionMenu(
            div_frame,
            variable=self.division_var,
            values=divisions,
            command=lambda _: self._on_change(),
            width=150
        )
        self.division_dropdown.pack(padx=5, pady=2)

    def _create_filter_status(self):
        """フィルタ状況表示を作成"""
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 5))
        self._update_filter_status()

    def _update_filter_status(self):
        """フィルタ状況表示を更新"""
        years = self.get_selected_years()
        division = self.division_var.get()

        years_str = ", ".join(f"{y}年" for y in years) if years else "未選択"

        self.status_label.configure(
            text=f"表示: {years_str} / {division}"
        )

    def _on_change(self):
        """フィルタ変更時"""
        self._update_filter_status()
        self.on_filter_change()

    def get_selected_years(self) -> List[int]:
        """選択された年度を取得"""
        return [year for year, var in self.year_vars.items() if var.get()]

    def get_selected_division(self) -> str:
        """選択された事業部を取得"""
        return self.division_var.get()

    def get_filter_values(self) -> Dict:
        """フィルタ値を取得"""
        return {
            "years": self.get_selected_years(),
            "divisions": [self.division_var.get()],  # 互換性のためリストで返す
            "division": self.division_var.get(),
            "account": "売上高"  # 互換性のため
        }

    def refresh(self):
        """フィルタを再作成（データ更新後）"""
        # 新しい年度を追加
        new_years = self.db.get_years()
        for year in new_years:
            if year not in self.year_vars:
                self.year_vars[year] = ctk.BooleanVar(value=True)

        # 事業部リストを更新
        divisions = self.db.get_divisions()
        self.division_dropdown.configure(values=divisions)


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
        set_status: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.db = db if db else AccountingDatabase()
        self._owns_db = db is None
        self.set_status = set_status

        # 選択中の取引先
        self.selected_customer: Optional[str] = None

        # レイアウト設定
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)  # フィルタ
        self.grid_rowconfigure(1, weight=1)  # メインエリア上段
        self.grid_rowconfigure(2, weight=1)  # メインエリア下段

        # フィルタパネルを作成
        self._create_filter_panel()

        # ウィジェットを作成
        self._create_widgets()

        # 初期データを表示
        self._update_data()

    def _create_filter_panel(self):
        """フィルタパネルを作成"""
        self.filter_panel = CustomerFilterPanel(
            self,
            db=self.db,
            on_filter_change=self._on_filter_change
        )
        self.filter_panel.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

    def _create_widgets(self):
        """ウィジェットを作成"""
        # 左: 取引先ランキングテーブル
        self.ranking_table = CustomerRankingTable(
            self,
            on_select=self._on_customer_select
        )
        self.ranking_table.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)

        # 右上: 業種別構成比グラフ
        self.industry_chart = PieChartFrame(
            self,
            figsize=(5, 3.5),
            dpi=100
        )
        self.industry_chart.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # 右下: 選択取引先の月次推移（売上・利益）
        self.customer_trend_chart = LineChartFrame(
            self,
            figsize=(5, 3.5),
            dpi=100
        )
        self.customer_trend_chart.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)

        # 初期メッセージ
        self.customer_trend_chart.ax.text(
            0.5, 0.5, "取引先を選択してください",
            ha="center", va="center", fontsize=12
        )
        self.customer_trend_chart.redraw()

    def _on_filter_change(self):
        """フィルタ変更時"""
        if self.set_status:
            self.set_status("グラフを更新中...", "normal")
        self._update_data()
        if self.set_status:
            self.set_status("更新完了", "normal")

    def _update_data(self):
        """データを更新"""
        filter_values = self.filter_panel.get_filter_values()
        years = filter_values["years"]
        division = filter_values["division"]

        if not years:
            return

        # 最新年度のデータを使用
        latest_year = max(years)

        # 取引先ランキングを更新
        self._update_ranking(latest_year, division)

        # 業種別構成比を更新
        self._update_industry_chart(latest_year, division)

        # 選択取引先があれば推移も更新
        if self.selected_customer:
            self._update_customer_profit_trend(self.selected_customer, latest_year, division)

    def _update_ranking(self, year: int, division: str):
        """取引先ランキングを更新"""
        df = self.db.get_customer_ranking_by_division(year, division, limit=20)

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

    def _update_industry_chart(self, year: int, division: str):
        """業種別構成比グラフを更新"""
        df = self.db.get_industry_summary_by_division(year, division)

        if df.empty:
            self.industry_chart.clear()
            self.industry_chart.set_title("業種別構成比（データなし）")
            self.industry_chart.redraw()
            return

        self.industry_chart.plot(
            labels=df["industry"].tolist(),
            values=df["total"].tolist(),
            title=f"業種別構成比 {year}年度 - {division}"
        )

    def _on_customer_select(self, customer_name: str, industry: str):
        """取引先選択時の処理"""
        filter_values = self.filter_panel.get_filter_values()
        years = filter_values["years"]
        division = filter_values["division"]

        if not years:
            return

        self.selected_customer = customer_name
        latest_year = max(years)
        self._update_customer_profit_trend(customer_name, latest_year, division)

    def _update_customer_profit_trend(self, customer_name: str, year: int, division: str):
        """選択取引先の月次売上・利益推移を更新"""
        conn = self.db.connection

        # 月次データを取得（売上・利益）
        months = list(range(1, 13))

        query = """
            SELECT
                month,
                SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) as sales,
                SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as cost,
                SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) -
                SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as profit
            FROM transactions_denormalized
            WHERE customer_name = ?
              AND year = ?
              AND division = ?
            GROUP BY month
            ORDER BY month
        """
        cursor = conn.execute(query, [customer_name, year, division])
        results = {row[0]: {"sales": row[1], "profit": row[3]} for row in cursor.fetchall()}

        y_data_dict = {}

        # 売上高データ
        sales_values = [results.get(m, {}).get("sales", 0) / 1_000_000 for m in months]
        profit_values = [results.get(m, {}).get("profit", 0) / 1_000_000 for m in months]

        y_data_dict["売上高"] = sales_values
        y_data_dict["売上総利益"] = profit_values

        if not any(sales_values) and not any(profit_values):
            self.customer_trend_chart.clear()
            self.customer_trend_chart.set_title("データなし")
            self.customer_trend_chart.redraw()
            return

        self.customer_trend_chart.plot(
            x_data=months,
            y_data_dict=y_data_dict,
            xlabel="月",
            ylabel="金額（百万円）",
            title=f"{customer_name} - 売上・利益推移 {year}年度 - {division}"
        )

    def get_filter_values(self) -> Dict:
        """フィルタ値を取得"""
        return self.filter_panel.get_filter_values()

    def refresh_filters(self):
        """フィルタを更新"""
        self.filter_panel.refresh()

    def destroy(self):
        """リソースを解放"""
        if self._owns_db and self.db:
            self.db.close()
        super().destroy()
