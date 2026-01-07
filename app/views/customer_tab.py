"""
取引先分析タブ - 取引先ランキングと業種別分析
フィルタ: 年度（複数選択）、事業部（単一選択）、業種（複数選択）
"""

from typing import Callable, Dict, List, Optional

import customtkinter as ctk
from tkinter import ttk
import numpy as np

from app.models.database import AccountingDatabase
from app.utils.chart_base import PieChartFrame, LineChartFrame, ChartFrame


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
        self.industry_vars: Dict[str, ctk.BooleanVar] = {}

        self._create_widgets()

    def _create_widgets(self):
        """ウィジェットを作成"""
        self.grid_columnconfigure((0, 1, 2), weight=1)

        self._create_year_filter()
        self._create_division_filter()
        self._create_industry_filter()
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
        """事業部フィルタを作成"""
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

        ctk.CTkButton(
            ind_frame, text="全選択", width=50, height=20,
            command=self._select_all_industries,
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=2)

        self.industry_checkbox_frame = ctk.CTkScrollableFrame(
            ind_frame,
            height=24,
            width=250,
            orientation="horizontal",
            fg_color="transparent"
        )
        self.industry_checkbox_frame.pack(side="left", padx=2)

        self._update_industry_checkboxes()

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
        industries = self.get_selected_industries()

        years_str = ", ".join(f"{y}年" for y in years) if years else "未選択"
        ind_str = "全業種" if len(industries) == len(self.industry_vars) else f"{len(industries)}業種" if industries else "未選択"

        self.status_label.configure(
            text=f"表示: {years_str} / {division} / {ind_str}"
        )

    def _on_division_change(self, _=None):
        """事業部変更時"""
        self._update_industry_checkboxes()
        self._on_change()

    def _update_industry_checkboxes(self):
        """業種チェックボックスを更新"""
        for widget in self.industry_checkbox_frame.winfo_children():
            widget.destroy()

        self.industry_vars.clear()

        years = self.get_selected_years()
        division = self.division_var.get()

        if not years or not division:
            return

        latest_year = max(years)
        df = self.db.get_industry_summary_by_division(latest_year, division)

        if df.empty:
            return

        for industry in df["industry"].tolist():
            var = ctk.BooleanVar(value=True)
            self.industry_vars[industry] = var
            cb = ctk.CTkCheckBox(
                self.industry_checkbox_frame,
                text=industry,
                variable=var,
                command=self._on_change,
                width=80,
                height=20,
                checkbox_width=16,
                checkbox_height=16,
                font=ctk.CTkFont(size=10)
            )
            cb.pack(side="left", padx=2)

    def _select_all_industries(self):
        """全業種を選択"""
        for var in self.industry_vars.values():
            var.set(True)
        self._on_change()

    def _on_change(self):
        """フィルタ変更時"""
        self._update_filter_status()
        self.on_filter_change()

    def get_selected_years(self) -> List[int]:
        return [year for year, var in self.year_vars.items() if var.get()]

    def get_selected_division(self) -> str:
        return self.division_var.get()

    def get_selected_industries(self) -> List[str]:
        return [ind for ind, var in self.industry_vars.items() if var.get()]

    def get_filter_values(self) -> Dict:
        return {
            "years": self.get_selected_years(),
            "divisions": [self.division_var.get()],
            "division": self.division_var.get(),
            "industries": self.get_selected_industries(),
            "account": "売上高"
        }

    def refresh(self):
        """フィルタを再作成"""
        new_years = self.db.get_years()
        for year in new_years:
            if year not in self.year_vars:
                self.year_vars[year] = ctk.BooleanVar(value=True)

        divisions = self.db.get_divisions()
        self.division_dropdown.configure(values=divisions)

        self._update_industry_checkboxes()


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

        style = ttk.Style()
        style.configure("Treeview", rowheight=22, font=("", 10))
        style.configure("Treeview.Heading", font=("", 10, "bold"))

        header = ctk.CTkLabel(
            self,
            text="取引先ランキング TOP20",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        header.pack(pady=(5, 3), anchor="w", padx=10)

        columns = ("rank", "customer", "industry", "amount")
        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=12
        )

        self.tree.heading("rank", text="順位")
        self.tree.heading("customer", text="取引先名")
        self.tree.heading("industry", text="業種")
        self.tree.heading("amount", text="金額")

        self.tree.column("rank", width=40, anchor="center")
        self.tree.column("customer", width=150)
        self.tree.column("industry", width=80)
        self.tree.column("amount", width=100, anchor="e")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=3)
        scrollbar.pack(side="right", fill="y", pady=3, padx=(0, 10))

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _on_tree_select(self, event):
        selection = self.tree.selection()
        if selection and self.on_select:
            item = self.tree.item(selection[0])
            values = item["values"]
            if len(values) >= 2:
                self.on_select(values[1], values[2])

    def update_data(self, data: list):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in data:
            self.tree.insert("", "end", values=row)


class CustomerTrendPanel(ctk.CTkFrame):
    """取引先推移グラフパネル（表示切替付き）"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.current_mode = "yearly"  # "yearly" or "continuous"
        self.cached_data = None

        # ヘッダー（タイトル + 切替ボタン）
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))

        self.title_label = ctk.CTkLabel(
            header_frame,
            text="取引先を選択してください",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.title_label.pack(side="left", padx=5)

        # 表示切替ボタン
        self.mode_var = ctk.StringVar(value="yearly")
        mode_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        mode_frame.pack(side="right", padx=5)

        ctk.CTkRadioButton(
            mode_frame,
            text="年度別",
            variable=self.mode_var,
            value="yearly",
            command=self._on_mode_change,
            width=70,
            height=20,
            radiobutton_width=14,
            radiobutton_height=14,
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=2)

        ctk.CTkRadioButton(
            mode_frame,
            text="月次推移",
            variable=self.mode_var,
            value="continuous",
            command=self._on_mode_change,
            width=70,
            height=20,
            radiobutton_width=14,
            radiobutton_height=14,
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=2)

        # グラフエリア
        self.chart = ChartFrame(self, figsize=(5, 2.5), dpi=100)
        self.chart.pack(fill="both", expand=True, padx=5, pady=5)

        # 初期メッセージ
        self.chart.ax.text(
            0.5, 0.5, "取引先を選択してください",
            ha="center", va="center", fontsize=10
        )
        self.chart.redraw()

    def _on_mode_change(self):
        """表示モード変更時"""
        self.current_mode = self.mode_var.get()
        if self.cached_data:
            self._render_chart()

    def update_data(self, customer_name: str, results: Dict, years: List[int]):
        """データを更新"""
        self.cached_data = {
            "customer_name": customer_name,
            "results": results,
            "years": years
        }
        self._render_chart()

    def _render_chart(self):
        """グラフを描画"""
        if not self.cached_data:
            return

        customer_name = self.cached_data["customer_name"]
        results = self.cached_data["results"]
        years = self.cached_data["years"]

        self.title_label.configure(text=f"{customer_name} - 売上・利益推移")

        if self.current_mode == "yearly":
            self._render_yearly_mode(results, years)
        else:
            self._render_continuous_mode(results, years)

    def _render_yearly_mode(self, results: Dict, years: List[int]):
        """年度別モード（月をX軸、年度ごとに線）"""
        self.chart.clear()
        ax = self.chart.ax

        months = list(range(1, 13))
        sorted_years = sorted(years)
        colors = ["#1976D2", "#4CAF50", "#FF9800", "#9C27B0"]

        # 各年度の売上を折れ線で
        for i, year in enumerate(sorted_years):
            if year in results:
                sales_values = [results[year].get(m, {}).get("sales", 0) / 1_000_000 for m in months]
                if any(sales_values):
                    ax.plot(months, sales_values, marker="o", markersize=3,
                            label=f"{year}年 売上", color=colors[i % len(colors)], linewidth=1.5)

        # 最新年の利益を破線で
        if sorted_years:
            latest_year = sorted_years[-1]
            if latest_year in results:
                profit_values = [results[latest_year].get(m, {}).get("profit", 0) / 1_000_000 for m in months]
                if any(profit_values):
                    ax.plot(months, profit_values, marker="s", markersize=3,
                            label=f"{latest_year}年 利益", color="#E53935",
                            linestyle="--", linewidth=1.5)

        ax.set_xlabel("月", fontsize=9)
        ax.set_ylabel("金額（百万円）", fontsize=9)
        ax.set_xticks(months)
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        ax.tick_params(labelsize=8)

        self.chart.figure.tight_layout()
        self.chart.redraw()

    def _render_continuous_mode(self, results: Dict, years: List[int]):
        """月次推移モード（年月をX軸）"""
        self.chart.clear()
        ax = self.chart.ax

        sorted_years = sorted(years)

        # X軸データを生成
        x_labels = []
        sales_values = []
        profit_values = []

        for year in sorted_years:
            for month in range(1, 13):
                x_labels.append(f"{year}/{month}")
                if year in results:
                    sales_values.append(results[year].get(month, {}).get("sales", 0) / 1_000_000)
                    profit_values.append(results[year].get(month, {}).get("profit", 0) / 1_000_000)
                else:
                    sales_values.append(0)
                    profit_values.append(0)

        x_indices = list(range(len(x_labels)))

        # 売上は棒グラフ
        ax.bar(x_indices, sales_values, color="#1976D2", alpha=0.7, label="売上高", width=0.8)

        # 利益は折れ線
        ax2 = ax.twinx()
        ax2.plot(x_indices, profit_values, color="#E53935", marker="o", markersize=2,
                 label="売上総利益", linewidth=1.5)

        ax.set_xlabel("年月", fontsize=9)
        ax.set_ylabel("売上（百万円）", fontsize=9, color="#1976D2")
        ax2.set_ylabel("利益（百万円）", fontsize=9, color="#E53935")

        # X軸ラベルを間引く
        tick_positions = list(range(0, len(x_labels), 3))
        ax.set_xticks(tick_positions)
        ax.set_xticklabels([x_labels[i] for i in tick_positions], rotation=45, ha="right", fontsize=7)

        ax.tick_params(labelsize=8)
        ax2.tick_params(labelsize=8)

        # 凡例を統合
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=8)

        ax.grid(axis="y", alpha=0.3)
        self.chart.figure.tight_layout()
        self.chart.redraw()

    def clear(self):
        """グラフをクリア"""
        self.cached_data = None
        self.title_label.configure(text="取引先を選択してください")
        self.chart.clear()
        self.chart.ax.text(
            0.5, 0.5, "取引先を選択してください",
            ha="center", va="center", fontsize=10
        )
        self.chart.redraw()


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

        self.selected_customer: Optional[str] = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._create_filter_panel()
        self._create_widgets()
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

        # 左下: 選択取引先の推移（切替付き）
        self.customer_trend_panel = CustomerTrendPanel(self)
        self.customer_trend_panel.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        # 右上: 業種別構成比グラフ
        self.industry_chart = PieChartFrame(
            self,
            figsize=(5, 3),
            dpi=100
        )
        self.industry_chart.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # 右下: 業種別月次推移グラフ
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
        industries = filter_values["industries"]

        if not years:
            return

        latest_year = max(years)

        self._update_ranking(latest_year, division, industries)
        self._update_industry_chart(latest_year, division, industries)
        self._update_industry_trend(years, division, industries)

        if self.selected_customer:
            self._update_customer_profit_trend(self.selected_customer, years, division)

    def _update_ranking(self, year: int, division: str, industries: List[str]):
        """取引先ランキングを更新"""
        if industries:
            df = self._get_customer_ranking_by_industries(year, division, industries)
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

    def _get_customer_ranking_by_industries(self, year: int, division: str, industries: List[str]):
        """業種フィルタ付き取引先ランキングを取得"""
        import pandas as pd
        conn = self.db.connection

        placeholders = ",".join("?" * len(industries))
        query = f"""
            SELECT customer_name, industry, SUM(amount) as total
            FROM transactions_denormalized
            WHERE account = '売上高'
              AND year = ?
              AND division = ?
              AND industry IN ({placeholders})
            GROUP BY customer_code, customer_name, industry
            ORDER BY total DESC
            LIMIT 20
        """
        params = [year, division] + industries
        return pd.read_sql_query(query, conn, params=params)

    def _update_industry_chart(self, year: int, division: str, industries: List[str]):
        """業種別構成比グラフを更新"""
        df = self.db.get_industry_summary_by_division(year, division)

        if df.empty:
            self.industry_chart.clear()
            self.industry_chart.set_title("業種別構成比（データなし）")
            self.industry_chart.redraw()
            return

        if industries:
            df = df[df["industry"].isin(industries)]

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

    def _update_industry_trend(self, years: List[int], division: str, industries: List[str]):
        """業種別月次推移グラフを更新"""
        if not industries:
            self.industry_trend_chart.clear()
            self.industry_trend_chart.ax.text(
                0.5, 0.5, "業種を選択してください",
                ha="center", va="center", fontsize=10
            )
            self.industry_trend_chart.redraw()
            return

        import pandas as pd
        conn = self.db.connection

        placeholders_years = ",".join("?" * len(years))
        placeholders_industries = ",".join("?" * len(industries))
        query = f"""
            SELECT year, month, industry, SUM(amount) as total
            FROM transactions_denormalized
            WHERE account = '売上高'
              AND year IN ({placeholders_years})
              AND division = ?
              AND industry IN ({placeholders_industries})
            GROUP BY year, month, industry
            ORDER BY year, month
        """
        params = years + [division] + industries
        df = pd.read_sql_query(query, conn, params=params)

        if df.empty:
            self.industry_trend_chart.clear()
            self.industry_trend_chart.set_title("業種別月次推移（データなし）")
            self.industry_trend_chart.redraw()
            return

        sorted_years = sorted(years)
        x_labels = []
        x_indices = []
        idx = 0
        for year in sorted_years:
            for month in range(1, 13):
                x_labels.append(f"{year}/{month}")
                x_indices.append(idx)
                idx += 1

        y_data_dict = {}
        for industry in industries:
            ind_data = df[df["industry"] == industry]
            values = []
            for year in sorted_years:
                for month in range(1, 13):
                    row = ind_data[(ind_data["year"] == year) & (ind_data["month"] == month)]
                    if not row.empty:
                        values.append(row["total"].values[0] / 1_000_000)
                    else:
                        values.append(0)
            if any(values):
                y_data_dict[industry] = values

        if not y_data_dict:
            self.industry_trend_chart.clear()
            self.industry_trend_chart.set_title("業種別月次推移（データなし）")
            self.industry_trend_chart.redraw()
            return

        self.industry_trend_chart.plot(
            x_data=x_indices,
            y_data_dict=y_data_dict,
            xlabel="年月",
            ylabel="売上（百万円）",
            title=f"業種別月次推移 - {division}"
        )

        ax = self.industry_trend_chart.ax
        ax.set_xticks(x_indices[::3])
        ax.set_xticklabels([x_labels[i] for i in range(0, len(x_labels), 3)], rotation=45, ha="right", fontsize=8)
        self.industry_trend_chart.figure.tight_layout()
        self.industry_trend_chart.redraw()

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
        """選択取引先の月次売上・利益推移を更新"""
        conn = self.db.connection

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

        if not results:
            self.customer_trend_panel.clear()
            return

        self.customer_trend_panel.update_data(customer_name, results, years)

    def get_filter_values(self) -> Dict:
        return self.filter_panel.get_filter_values()

    def refresh_filters(self):
        self.filter_panel.refresh()

    def destroy(self):
        if self._owns_db and self.db:
            self.db.close()
        super().destroy()
