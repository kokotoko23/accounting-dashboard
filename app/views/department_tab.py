"""
部門分析タブ - 事業部内の部門別分析
フィルタ: 年度（複数選択）、事業部（単一選択）、部門（複数選択）、科目
"""

from typing import Callable, Dict, List, Optional

import customtkinter as ctk

from app.models.database import AccountingDatabase
from app.utils.chart_base import LineChartFrame, BarChartFrame, PieChartFrame


class DepartmentFilterPanel(ctk.CTkFrame):
    """部門分析用フィルタパネル"""

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
        self.dept_vars: Dict[str, ctk.BooleanVar] = {}  # dept_code -> BooleanVar
        self.dept_names: Dict[str, str] = {}  # dept_code -> dept_name
        self.account_var = ctk.StringVar()

        self._create_widgets()

    def _create_widgets(self):
        """ウィジェットを作成"""
        # 横並びレイアウト
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # 年度フィルタ
        self._create_year_filter()

        # 事業部フィルタ（単一選択）
        self._create_division_filter()

        # 部門フィルタ
        self._create_dept_filter()

        # 科目フィルタ
        self._create_account_filter()

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

    def _create_dept_filter(self):
        """部門フィルタを作成"""
        self.dept_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dept_frame.grid(row=0, column=2, sticky="w", padx=5, pady=2)

        ctk.CTkLabel(
            self.dept_frame, text="部門:", font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=(5, 2))

        ctk.CTkButton(
            self.dept_frame, text="全選択", width=50, height=20,
            command=self._select_all_depts,
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=2)

        # 部門チェックボックス用のフレーム（横スクロール）
        self.dept_checkbox_frame = ctk.CTkScrollableFrame(
            self.dept_frame,
            height=24,
            width=200,
            orientation="horizontal",
            fg_color="transparent"
        )
        self.dept_checkbox_frame.pack(side="left", padx=2)

        # 初期の部門リストを作成
        self._update_dept_checkboxes()

    def _create_account_filter(self):
        """科目フィルタを作成"""
        account_frame = ctk.CTkFrame(self, fg_color="transparent")
        account_frame.grid(row=0, column=3, sticky="w", padx=5, pady=2)

        ctk.CTkLabel(
            account_frame, text="科目:", font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=(5, 2))

        accounts = self.db.get_accounts()
        self.account_var.set(accounts[0] if accounts else "売上高")

        self.account_dropdown = ctk.CTkOptionMenu(
            account_frame,
            variable=self.account_var,
            values=accounts,
            command=lambda _: self._on_change(),
            width=100,
            height=24
        )
        self.account_dropdown.pack(side="left", padx=2)

    def _create_filter_status(self):
        """フィルタ状況表示を作成"""
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.status_label.grid(row=1, column=0, columnspan=4, sticky="w", padx=10, pady=(0, 2))
        self._update_filter_status()

    def _update_filter_status(self):
        """フィルタ状況表示を更新"""
        years = self.get_selected_years()
        division = self.division_var.get()
        depts = self.get_selected_depts()
        account = self.account_var.get()

        years_str = ", ".join(f"{y}年" for y in years) if years else "未選択"
        dept_str = "全部門" if len(depts) == len(self.dept_vars) else f"{len(depts)}部門" if depts else "未選択"

        self.status_label.configure(
            text=f"表示: {years_str} / {division} / {dept_str} / {account}"
        )

    def _update_dept_checkboxes(self):
        """部門チェックボックスを更新"""
        # 既存のウィジェットを削除
        for widget in self.dept_checkbox_frame.winfo_children():
            widget.destroy()

        self.dept_vars.clear()
        self.dept_names.clear()

        # 選択中の事業部の部門を取得
        division = self.division_var.get()
        if not division:
            return

        df = self.db.get_depts_by_division(division)

        for _, row in df.iterrows():
            dept_code = row["dept_code"]
            dept_name = row["dept_name"]
            self.dept_names[dept_code] = dept_name

            var = ctk.BooleanVar(value=True)
            self.dept_vars[dept_code] = var
            cb = ctk.CTkCheckBox(
                self.dept_checkbox_frame,
                text=dept_name,
                variable=var,
                command=self._on_change,
                width=100,
                height=20,
                checkbox_width=16,
                checkbox_height=16,
                font=ctk.CTkFont(size=10)
            )
            cb.pack(side="left", padx=2)

    def _on_division_change(self, _=None):
        """事業部変更時"""
        self._update_dept_checkboxes()
        self._on_change()

    def _select_all_depts(self):
        """全部門を選択"""
        for var in self.dept_vars.values():
            var.set(True)
        self._on_change()

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

    def get_selected_depts(self) -> List[str]:
        """選択された部門コードを取得"""
        return [code for code, var in self.dept_vars.items() if var.get()]

    def get_selected_dept_names(self) -> Dict[str, str]:
        """選択された部門の{コード: 名前}を取得"""
        return {code: self.dept_names[code] for code in self.get_selected_depts()}

    def get_filter_values(self) -> Dict:
        """フィルタ値を取得"""
        return {
            "years": self.get_selected_years(),
            "divisions": [self.division_var.get()],  # 互換性のためリストで返す
            "division": self.division_var.get(),
            "dept_codes": self.get_selected_depts(),
            "account": self.account_var.get()
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

        # 部門リストを更新
        self._update_dept_checkboxes()


class DepartmentTab(ctk.CTkFrame):
    """部門分析タブコンポーネント"""

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

        # グリッド設定
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)  # フィルタ
        self.grid_rowconfigure(1, weight=1)  # グラフ上段
        self.grid_rowconfigure(2, weight=1)  # グラフ下段

        # フィルタパネルを作成
        self._create_filter_panel()

        # グラフを作成
        self._create_charts()

        # 初期データを表示
        self._update_charts()

    def _create_filter_panel(self):
        """フィルタパネルを作成"""
        self.filter_panel = DepartmentFilterPanel(
            self,
            db=self.db,
            on_filter_change=self._on_filter_change
        )
        self.filter_panel.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

    def _create_charts(self):
        """グラフを作成"""
        # 左上: 部門別構成比（円グラフ）
        self.dept_pie = PieChartFrame(self, figsize=(5, 3.5), dpi=100)
        self.dept_pie.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # 右上: 部門別売上・利益（棒グラフ）
        self.profit_bar = BarChartFrame(self, figsize=(5, 3.5), dpi=100)
        self.profit_bar.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # 左下: 年度別月次推移（折れ線）
        self.yearly_trend = LineChartFrame(self, figsize=(5, 3.5), dpi=100)
        self.yearly_trend.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        # 右下: 部門別月次推移（折れ線）
        self.dept_trend = LineChartFrame(self, figsize=(5, 3.5), dpi=100)
        self.dept_trend.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)

    def _on_filter_change(self):
        """フィルタ変更時"""
        if self.set_status:
            self.set_status("グラフを更新中...", "normal")
        self._update_charts()
        if self.set_status:
            self.set_status("更新完了", "normal")

    def _update_charts(self):
        """全グラフを更新"""
        filter_values = self.filter_panel.get_filter_values()
        years = filter_values["years"]
        division = filter_values["division"]
        dept_codes = filter_values["dept_codes"]
        account = filter_values["account"]

        self._update_dept_pie(years, division, account)
        self._update_profit_bar(years, division, dept_codes)
        self._update_yearly_trend(years, division, dept_codes, account)
        self._update_dept_trend(years, division, dept_codes, account)

    def _update_dept_pie(self, years: List[int], division: str, account: str):
        """部門別構成比を更新"""
        if not years or not division:
            self.dept_pie.clear()
            self.dept_pie.set_title("部門構成比（データなし）")
            self.dept_pie.redraw()
            return

        df = self.db.get_dept_summary_by_division(years, division, account)

        if df.empty:
            self.dept_pie.clear()
            self.dept_pie.set_title("部門構成比（データなし）")
            self.dept_pie.redraw()
            return

        self.dept_pie.plot(
            labels=df["dept_name"].tolist(),
            values=df["total"].tolist(),
            title=f"部門構成比 - {division} - {account}"
        )

    def _update_profit_bar(self, years: List[int], division: str, dept_codes: List[str]):
        """部門別売上・利益グラフを更新"""
        if not years or not division:
            self.profit_bar.clear()
            self.profit_bar.set_title("売上・利益（データなし）")
            self.profit_bar.redraw()
            return

        df = self.db.get_dept_profit_summary_by_division(years, division, dept_codes if dept_codes else None)

        if df.empty:
            self.profit_bar.clear()
            self.profit_bar.set_title("売上・利益（データなし）")
            self.profit_bar.redraw()
            return

        self._plot_grouped_bar(
            df["dept_name"].tolist(),
            {
                "売上高": [v / 1_000_000 for v in df["sales"].tolist()],
                "売上総利益": [v / 1_000_000 for v in df["profit"].tolist()]
            },
            f"部門別 売上・利益 - {division}"
        )

    def _plot_grouped_bar(self, labels: List[str], data_dict: dict, title: str):
        """グループ化された棒グラフを描画"""
        import numpy as np

        self.profit_bar.clear()
        ax = self.profit_bar.ax

        n_groups = len(labels)
        n_bars = len(data_dict)

        if n_groups == 0:
            return

        total_width = 0.8
        width = total_width / n_bars
        x = np.arange(n_groups)

        colors = ["#1976D2", "#4CAF50"]

        for i, (label, values) in enumerate(data_dict.items()):
            offset = (i - n_bars / 2 + 0.5) * width
            ax.bar(x + offset, values, width, label=label, color=colors[i % len(colors)])

        ax.set_xlabel("部門")
        ax.set_ylabel("金額（百万円）")
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.legend(loc="upper right")
        ax.grid(axis="y", alpha=0.3)

        self.profit_bar.figure.tight_layout()
        self.profit_bar.redraw()

    def _update_yearly_trend(self, years: List[int], division: str, dept_codes: List[str], account: str):
        """年度別月次推移を更新"""
        if not years or not division or not dept_codes:
            self.yearly_trend.clear()
            self.yearly_trend.set_title("月次推移（データなし）")
            self.yearly_trend.redraw()
            return

        df = self.db.get_dept_monthly_data(years, division, dept_codes, account)

        if df.empty:
            self.yearly_trend.clear()
            self.yearly_trend.set_title("月次推移（データなし）")
            self.yearly_trend.redraw()
            return

        # 年度別に集計
        months = list(range(1, 13))
        y_data_dict = {}

        for year in sorted(years):
            year_data = df[df["year"] == year]
            monthly_values = []
            for month in months:
                month_data = year_data[year_data["month"] == month]
                if not month_data.empty:
                    monthly_values.append(month_data["total"].sum() / 1_000_000)
                else:
                    monthly_values.append(0)
            y_data_dict[f"{year}年"] = monthly_values

        self.yearly_trend.plot(
            x_data=months,
            y_data_dict=y_data_dict,
            xlabel="月",
            ylabel="金額（百万円）",
            title=f"年度別月次推移 - {division} - {account}"
        )

    def _update_dept_trend(self, years: List[int], division: str, dept_codes: List[str], account: str):
        """部門別月次推移を更新"""
        if not years or not division or not dept_codes:
            self.dept_trend.clear()
            self.dept_trend.set_title("部門別推移（データなし）")
            self.dept_trend.redraw()
            return

        latest_year = max(years)
        df = self.db.get_dept_monthly_data([latest_year], division, dept_codes, account)

        if df.empty:
            self.dept_trend.clear()
            self.dept_trend.set_title("部門別推移（データなし）")
            self.dept_trend.redraw()
            return

        months = list(range(1, 13))
        y_data_dict = {}

        dept_names = self.filter_panel.get_selected_dept_names()

        for dept_code in dept_codes:
            dept_data = df[df["dept_code"] == dept_code]
            if not dept_data.empty:
                dept_name = dept_names.get(dept_code, dept_code)
                monthly_values = []
                for month in months:
                    month_data = dept_data[dept_data["month"] == month]
                    if not month_data.empty:
                        monthly_values.append(month_data["total"].values[0] / 1_000_000)
                    else:
                        monthly_values.append(0)
                y_data_dict[dept_name] = monthly_values

        if not y_data_dict:
            self.dept_trend.clear()
            self.dept_trend.set_title("部門別推移（データなし）")
            self.dept_trend.redraw()
            return

        self.dept_trend.plot(
            x_data=months,
            y_data_dict=y_data_dict,
            xlabel="月",
            ylabel="金額（百万円）",
            title=f"部門別推移 {latest_year}年 - {division} - {account}"
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
