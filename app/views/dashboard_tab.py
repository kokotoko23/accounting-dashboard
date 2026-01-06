"""
ダッシュボードタブ - 2x2グリッドでグラフを配置
"""

from typing import List, Optional

import customtkinter as ctk
import pandas as pd

from app.models.database import AccountingDatabase
from app.utils.chart_base import LineChartFrame, BarChartFrame, PieChartFrame
from app.views.summary_panel import SummaryPanel


class DashboardTab(ctk.CTkFrame):
    """ダッシュボードタブコンポーネント"""

    def __init__(self, parent, db: Optional[AccountingDatabase] = None, **kwargs):
        """
        ダッシュボードタブを初期化

        Args:
            parent: 親ウィジェット
            db: データベース接続（Noneの場合は新規作成）
        """
        super().__init__(parent, **kwargs)

        # データベース接続
        self.db = db if db else AccountingDatabase()
        self._owns_db = db is None  # 自分で作成した場合はクローズ責任を持つ

        # グリッド設定（サマリー + 2x2グラフ）
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)  # サマリーパネル
        self.grid_rowconfigure(1, weight=1)  # グラフ上段
        self.grid_rowconfigure(2, weight=1)  # グラフ下段

        # サマリーパネルを作成
        self._create_summary_panel()

        # グラフフレームを作成
        self._create_charts()

    def _create_summary_panel(self):
        """サマリーパネルを作成"""
        self.summary_panel = SummaryPanel(self, db=self.db)
        self.summary_panel.grid(
            row=0, column=0, columnspan=2,
            sticky="ew", padx=5, pady=5
        )

    def _create_charts(self):
        """グラフを作成"""
        # 左上: 月次推移グラフ（折れ線）
        self.monthly_chart = LineChartFrame(
            self,
            figsize=(5, 3),
            dpi=100
        )
        self.monthly_chart.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # 右上: セグメント構成比（円グラフ）
        self.segment_chart = PieChartFrame(
            self,
            figsize=(5, 3),
            dpi=100
        )
        self.segment_chart.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # 左下: 前年同月比較（棒グラフ）
        self.comparison_chart = BarChartFrame(
            self,
            figsize=(5, 3),
            dpi=100
        )
        self.comparison_chart.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        # 右下: 予備スペース（折れ線）
        self.extra_chart = LineChartFrame(
            self,
            figsize=(5, 3),
            dpi=100
        )
        self.extra_chart.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)

    def update_charts(
        self,
        years: List[int],
        segments: List[str],
        account: str
    ):
        """
        全グラフとサマリーを更新

        Args:
            years: 選択された年度リスト
            segments: 選択されたセグメントリスト
            account: 選択された科目
        """
        # サマリーパネルを更新
        self.summary_panel.update_summary(years, segments, account)

        # グラフを更新
        self._update_monthly_chart(years, segments, account)
        self._update_segment_chart(years, account)
        self._update_comparison_chart(years, segments, account)
        self._update_extra_chart(years, segments, account)

    def _update_monthly_chart(
        self,
        years: List[int],
        segments: List[str],
        account: str
    ):
        """月次推移グラフを更新"""
        if not years or not segments:
            self.monthly_chart.clear()
            self.monthly_chart.set_title("月次推移（データなし）")
            self.monthly_chart.redraw()
            return

        # データ取得
        df = self.db.get_monthly_data(years, segments, account)

        if df.empty:
            self.monthly_chart.clear()
            self.monthly_chart.set_title("月次推移（データなし）")
            self.monthly_chart.redraw()
            return

        # 年度ごとにデータを整理
        months = list(range(1, 13))
        y_data_dict = {}

        for year in sorted(years):
            year_data = df[df["year"] == year]
            # 月ごとのデータを取得（データがない月は0）
            monthly_values = []
            for month in months:
                month_data = year_data[year_data["month"] == month]
                if not month_data.empty:
                    monthly_values.append(month_data["total"].values[0] / 1_000_000)  # 百万円単位
                else:
                    monthly_values.append(0)
            y_data_dict[f"{year}年度"] = monthly_values

        # グラフ描画
        self.monthly_chart.plot(
            x_data=months,
            y_data_dict=y_data_dict,
            xlabel="月",
            ylabel="金額（百万円）",
            title=f"月次推移 - {account}"
        )

    def _update_segment_chart(self, years: List[int], account: str):
        """セグメント構成比グラフを更新"""
        if not years:
            self.segment_chart.clear()
            self.segment_chart.set_title("セグメント構成比（データなし）")
            self.segment_chart.redraw()
            return

        # データ取得
        df = self.db.get_segment_summary(years, account)

        if df.empty:
            self.segment_chart.clear()
            self.segment_chart.set_title("セグメント構成比（データなし）")
            self.segment_chart.redraw()
            return

        # グラフ描画
        self.segment_chart.plot(
            labels=df["segment"].tolist(),
            values=df["total"].tolist(),
            title=f"セグメント構成比 - {account}"
        )

    def _update_comparison_chart(
        self,
        years: List[int],
        segments: List[str],
        account: str
    ):
        """前年同月比較グラフを更新"""
        if not years or not segments or len(years) < 2:
            self.comparison_chart.clear()
            self.comparison_chart.set_title("前年比較（2年以上選択してください）")
            self.comparison_chart.redraw()
            return

        # 最新2年のデータを取得
        sorted_years = sorted(years)
        current_year = sorted_years[-1]
        prev_year = sorted_years[-2]

        df = self.db.get_monthly_data([current_year, prev_year], segments, account)

        if df.empty:
            self.comparison_chart.clear()
            self.comparison_chart.set_title("前年比較（データなし）")
            self.comparison_chart.redraw()
            return

        # 前年比を計算
        months = list(range(1, 13))
        month_labels = [f"{m}月" for m in months]
        comparison_values = []

        for month in months:
            current_data = df[(df["year"] == current_year) & (df["month"] == month)]
            prev_data = df[(df["year"] == prev_year) & (df["month"] == month)]

            if not current_data.empty and not prev_data.empty:
                current_val = current_data["total"].values[0]
                prev_val = prev_data["total"].values[0]
                if prev_val > 0:
                    ratio = (current_val / prev_val) * 100
                    comparison_values.append(ratio)
                else:
                    comparison_values.append(0)
            else:
                comparison_values.append(0)

        # グラフ描画
        self.comparison_chart.plot(
            labels=month_labels,
            values=comparison_values,
            xlabel="月",
            ylabel="前年比（%）",
            title=f"前年比較 {current_year}年 vs {prev_year}年 - {account}"
        )

    def _update_extra_chart(
        self,
        years: List[int],
        segments: List[str],
        account: str
    ):
        """予備グラフを更新（セグメント別月次推移）"""
        if not years or not segments:
            self.extra_chart.clear()
            self.extra_chart.set_title("セグメント別推移（データなし）")
            self.extra_chart.redraw()
            return

        # 最新年度のセグメント別月次データを取得
        latest_year = max(years)

        # セグメントごとにデータを取得
        months = list(range(1, 13))
        y_data_dict = {}

        for segment in segments:
            df = self.db.get_monthly_data([latest_year], [segment], account)
            if not df.empty:
                monthly_values = []
                for month in months:
                    month_data = df[df["month"] == month]
                    if not month_data.empty:
                        monthly_values.append(month_data["total"].values[0] / 1_000_000)
                    else:
                        monthly_values.append(0)
                y_data_dict[segment] = monthly_values

        if not y_data_dict:
            self.extra_chart.clear()
            self.extra_chart.set_title("セグメント別推移（データなし）")
            self.extra_chart.redraw()
            return

        # グラフ描画
        self.extra_chart.plot(
            x_data=months,
            y_data_dict=y_data_dict,
            xlabel="月",
            ylabel="金額（百万円）",
            title=f"セグメント別推移 {latest_year}年度 - {account}"
        )

    def destroy(self):
        """リソースを解放"""
        if self._owns_db and self.db:
            self.db.close()
        super().destroy()
