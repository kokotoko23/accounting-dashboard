"""
取引先分析タブ - 取引先ランキングと業種別分析
フィルタ: 年度（複数選択）、事業部（単一選択）、業種（単一選択）
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
        self.industry_var = ctk.StringVar()

        self._create_widgets()

    def _create_widgets(self):
        """ウィジェットを作成"""
        # 横並びレイアウト
        self.grid_columnconfigure((0, 1, 2), weight=1)

        # 年度フィルタ
        self._create_year_filter()

        # 事業部フィルタ（単一選択）
        self._create_division_filter()

        # 業種フィルタ（単一選択）
        self._create_industry_filter()

        # フィルタ状況表示
        self._create_filter_status()

    def _create_year_filter(self):
        """年度フィルタを作成"""
        year_frame = ctk.CTkFrame(self, fg_color="transparent")
        year_frame.grid(row=0, column=0, sticky="w", padx=5, pady=2)

        ctk.CTkLabel(
            year_frame, text="年度:", font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=(5, 2))

        years = self.db.get_years()
        for year in years:
            var = ctk.BooleanVar(value=True)
            self.year_vars[year] = var
            cb = ctk.CTkCheckBox(
                year_frame,
                text=f"{year}",
                variable=var,
                command=self._on_change,
                width=55,
                height=20,
                checkbox_width=16,
                checkbox_height=16
            )
            cb.pack(side="left", padx=2)

    def _create_division_filter(self):
        """事業部フィルタを作成（単一選択ドロップダウン）"""
        div_frame = ctk.CTkFrame(self, fg_color="transparent")
        div_frame.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        ctk.CTkLabel(
            div_frame, text="事業部:", font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=(5, 2))

        divisions = self.db.get_divisions()
        self.division_var.set(divisions[0] if divisions else "")

        self.division_dropdown = ctk.CTkOptionMenu(
            div_frame,
            variable=self.division_var,
            values=divisions,
            command=self._on_division_change,
            width=120,
            height=24
        )
        self.division_dropdown.pack(side="left", padx=2)

    def _create_industry_filter(self):
        """業種フィルタを作成"""
        ind_frame = ctk.CTkFrame(self, fg_color="transparent")
        ind_frame.grid(row=0, column=2, sticky="w", padx=5, pady=2)

        ctk.CTkLabel(
            ind_frame, text="業種:", font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=(5, 2))

        self.industry_var.set("全業種")

        self.industry_dropdown = ctk.CTkOptionMenu(
            ind_frame,
            variable=self.industry_var,
            values=["全業種"],
            command=lambda _: self._on_change(),
            width=120,
            height=24
        )
        self.industry_dropdown.pack(side="left", padx=2)

        # 初期の業種リストを更新
        self._update_industry_list()

    def _create_filter_status(self):
        """フィルタ状況表示を作成"""
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.status_label.grid(row=1, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 2))
        self._update_filter_status()

    def _update_filter_status(self):
        """フィルタ状況表示を更新"""
        years = self.get_selected_years()
        division = self.division_var.get()
        industry = self.industry_var.get()

        years_str = ", ".join(f"{y}年" for y in years) if years else "未選択"

        self.status_label.configure(
            text=f"表示: {years_str} / {division} / {industry}"
        )

    def _on_division_change(self, _=None):
        """事業部変更時"""
        self._update_industry_list()
        self._on_change()

    def _update_industry_list(self):
        """業種リストを更新"""
        years = self.get_selected_years()
        division = self.division_var.get()

        if not years or not division:
            return

        latest_year = max(years)
        df = self.db.get_industry_summary_by_division(latest_year, division)

        industries = ["全業種"] + df["industry"].tolist() if not df.empty else ["全業種"]
        self.industry_dropdown.configure(values=industries)

        if self.industry_var.get() not in industries:
            self.industry_var.set("全業種")

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

    def get_selected_industry(self) -> Optional[str]:
        """選択された業種を取得（全業種の場合はNone）"""
        industry = self.industry_var.get()
        return None if industry == "全業種" else industry

    def get_filter_values(self) -> Dict:
        """フィルタ値を取得"""
        return {
            "years": self.get_selected_years(),
            "divisions": [self.division_var.get()],
            "division": self.division_var.get(),
            "industry": self.get_selected_industry(),
            "account": "売上高"
        }

    def refresh(self):
        """フィルタを再作成（データ更新後）"""
        new_years = self.db.get_years()
        for year in new_years:
            if year not in self.year_vars:
                self.year_vars[year] = ctk.BooleanVar(value=True)

        divisions = self.db.get_divisions()
        self.division_dropdown.configure(values=divisions)

        self._update_industry_list()


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
        style.configure("Treeview", rowheight=22, font=("", 10))
        style.configure("Treeview.Heading", font=("", 10, "bold"))

        # ヘッダーラベル
        header = ctk.CTkLabel(
            self,
            text="取引先ランキング TOP20",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        header.pack(pady=(5, 3), anchor="w", padx=10)

        # Treeview作成
        columns = ("rank", "customer", "industry", "amount")
        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=12
        )

        # 列の設定
        self.tree.heading("rank", text="順位")
        self.tree.heading("customer", text="取引先名")
        self.tree.heading("industry", text="業種")
        self.tree.heading("amount", text="金額")

        self.tree.column("rank", width=40, anchor="center")
        self.tree.column("customer", width=150)
        self.tree.column("industry", width=80)
        self.tree.column("amount", width=100, anchor="e")

        # スクロールバー
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=3)
        scrollbar.pack(side="right", fill="y", pady=3, padx=(0, 10))

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
        """データを更新"""
        for item in self.tree.get_children():
            self.tree.delete(item)

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

        # レイアウト設定（左右2列、上下2行）
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)  # フィルタ
        self.grid_rowconfigure(1, weight=1)  # 上段
        self.grid_rowconfigure(2, weight=1)  # 下段

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
        # 左上: 取引先ランキングテーブル
        self.ranking_table = CustomerRankingTable(
            self,
            on_select=self._on_customer_select
        )
        self.ranking_table.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # 左下: 選択取引先の月次推移（複数年対応）
        self.customer_trend_chart = LineChartFrame(
            self,
            figsize=(5, 3),
            dpi=100
        )
        self.customer_trend_chart.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        # 初期メッセージ
        self.customer_trend_chart.ax.text(
            0.5, 0.5, "取引先を選択してください",
            ha="center", va="center", fontsize=12
        )
        self.customer_trend_chart.redraw()

        # 右上: 業種別構成比グラフ
        self.industry_chart = PieChartFrame(
            self,
            figsize=(5, 3),
            dpi=100
        )
        self.industry_chart.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # 右下: 業種別成長推移グラフ
        self.industry_trend_chart = LineChartFrame(
            self,
            figsize=(5, 3),
            dpi=100
        )
        self.industry_trend_chart.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)

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
        industry = filter_values["industry"]

        if not years:
            return

        latest_year = max(years)

        # 取引先ランキングを更新（業種フィルタ適用）
        self._update_ranking(latest_year, division, industry)

        # 業種別構成比を更新
        self._update_industry_chart(latest_year, division)

        # 業種別成長推移を更新
        self._update_industry_trend(years, division)

        # 選択取引先があれば推移も更新（複数年対応）
        if self.selected_customer:
            self._update_customer_profit_trend(self.selected_customer, years, division)

    def _update_ranking(self, year: int, division: str, industry: Optional[str]):
        """取引先ランキングを更新"""
        if industry:
            # 業種フィルタあり
            df = self._get_customer_ranking_by_industry(year, division, industry)
        else:
            df = self.db.get_customer_ranking_by_division(year, division, limit=20)

        if df.empty:
            self.ranking_table.update_data([])
            return

        data = []
        for i, row in df.iterrows():
            rank = i + 1
            customer = row["customer_name"]
            ind = row["industry"]
            amount = f"¥{int(row['total']):,}"
            data.append((rank, customer, ind, amount))

        self.ranking_table.update_data(data)

    def _get_customer_ranking_by_industry(self, year: int, division: str, industry: str):
        """業種別取引先ランキングを取得"""
        import pandas as pd
        conn = self.db.connection
        query = """
            SELECT customer_name, industry, SUM(amount) as total
            FROM transactions_denormalized
            WHERE account = '売上高'
              AND year = ?
              AND division = ?
              AND industry = ?
            GROUP BY customer_code, customer_name, industry
            ORDER BY total DESC
            LIMIT 20
        """
        return pd.read_sql_query(query, conn, params=[year, division, industry])

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
            title=f"業種別構成比 {year}年度"
        )

    def _update_industry_trend(self, years: List[int], division: str):
        """業種別成長推移グラフを更新"""
        if len(years) < 2:
            self.industry_trend_chart.clear()
            self.industry_trend_chart.ax.text(
                0.5, 0.5, "成長推移には2年以上のデータが必要です",
                ha="center", va="center", fontsize=10
            )
            self.industry_trend_chart.redraw()
            return

        import pandas as pd
        conn = self.db.connection

        # 年度別・業種別売上を取得
        placeholders = ",".join("?" * len(years))
        query = f"""
            SELECT year, industry, SUM(amount) as total
            FROM transactions_denormalized
            WHERE account = '売上高'
              AND year IN ({placeholders})
              AND division = ?
            GROUP BY year, industry
            ORDER BY year, total DESC
        """
        params = years + [division]
        df = pd.read_sql_query(query, conn, params=params)

        if df.empty:
            self.industry_trend_chart.clear()
            self.industry_trend_chart.set_title("業種別成長推移（データなし）")
            self.industry_trend_chart.redraw()
            return

        # 上位5業種を取得（最新年度基準）
        latest_year = max(years)
        top_industries = df[df["year"] == latest_year].nlargest(5, "total")["industry"].tolist()

        sorted_years = sorted(years)
        y_data_dict = {}

        for industry in top_industries:
            ind_data = df[df["industry"] == industry]
            values = []
            for year in sorted_years:
                year_data = ind_data[ind_data["year"] == year]
                if not year_data.empty:
                    values.append(year_data["total"].values[0] / 1_000_000)
                else:
                    values.append(0)
            y_data_dict[industry] = values

        if not y_data_dict:
            self.industry_trend_chart.clear()
            self.industry_trend_chart.set_title("業種別成長推移（データなし）")
            self.industry_trend_chart.redraw()
            return

        self.industry_trend_chart.plot(
            x_data=sorted_years,
            y_data_dict=y_data_dict,
            xlabel="年度",
            ylabel="売上（百万円）",
            title=f"業種別成長推移 TOP5 - {division}"
        )

    def _on_customer_select(self, customer_name: str, industry: str):
        """取引先選択時の処理"""
        filter_values = self.filter_panel.get_filter_values()
        years = filter_values["years"]
        division = filter_values["division"]

        if not years:
            return

        self.selected_customer = customer_name
        self._update_customer_profit_trend(customer_name, years, division)

    def _update_customer_profit_trend(self, customer_name: str, years: List[int], division: str):
        """選択取引先の月次売上・利益推移を更新（複数年対応）"""
        conn = self.db.connection
        months = list(range(1, 13))

        placeholders = ",".join("?" * len(years))
        query = f"""
            SELECT
                year, month,
                SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) as sales,
                SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as cost,
                SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) -
                SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as profit
            FROM transactions_denormalized
            WHERE customer_name = ?
              AND year IN ({placeholders})
              AND division = ?
            GROUP BY year, month
            ORDER BY year, month
        """
        params = [customer_name] + years + [division]
        cursor = conn.execute(query, params)
        results = {}
        for row in cursor.fetchall():
            year, month, sales, cost, profit = row
            if year not in results:
                results[year] = {}
            results[year][month] = {"sales": sales, "profit": profit}

        y_data_dict = {}
        sorted_years = sorted(years)

        for year in sorted_years:
            if year in results:
                sales_values = [results[year].get(m, {}).get("sales", 0) / 1_000_000 for m in months]
                if any(sales_values):
                    y_data_dict[f"{year}年 売上"] = sales_values

        # 最新年のみ利益も表示
        if sorted_years:
            latest_year = sorted_years[-1]
            if latest_year in results:
                profit_values = [results[latest_year].get(m, {}).get("profit", 0) / 1_000_000 for m in months]
                if any(profit_values):
                    y_data_dict[f"{latest_year}年 利益"] = profit_values

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
            title=f"{customer_name} - 売上推移"
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
