"""
ダッシュボードタブ - 2x2グリッドでグラフを配置
"""

import customtkinter as ctk

from app.utils.chart_base import LineChartFrame, BarChartFrame, PieChartFrame


class DashboardTab(ctk.CTkFrame):
    """ダッシュボードタブコンポーネント"""

    def __init__(self, parent, **kwargs):
        """
        ダッシュボードタブを初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent, **kwargs)

        # グリッド設定（2x2）
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # グラフフレームを作成
        self._create_charts()

        # ダミーデータで初期表示
        self._show_dummy_data()

    def _create_charts(self):
        """グラフを作成"""
        # 左上: 月次推移グラフ（折れ線）
        self.monthly_chart = LineChartFrame(
            self,
            figsize=(5, 3.5),
            dpi=100
        )
        self.monthly_chart.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # 右上: セグメント構成比（円グラフ）
        self.segment_chart = PieChartFrame(
            self,
            figsize=(5, 3.5),
            dpi=100
        )
        self.segment_chart.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # 左下: 前年同月比較（棒グラフ）
        self.comparison_chart = BarChartFrame(
            self,
            figsize=(5, 3.5),
            dpi=100
        )
        self.comparison_chart.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # 右下: 予備スペース（折れ線）
        self.extra_chart = LineChartFrame(
            self,
            figsize=(5, 3.5),
            dpi=100
        )
        self.extra_chart.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

    def _show_dummy_data(self):
        """ダミーデータを表示"""
        # 月次推移（折れ線グラフ）
        months = list(range(1, 13))
        self.monthly_chart.plot(
            x_data=months,
            y_data_dict={
                "2022年度": [100, 120, 110, 130, 125, 140, 135, 150, 145, 160, 155, 170],
                "2023年度": [110, 130, 120, 140, 135, 150, 145, 160, 155, 170, 165, 180],
                "2024年度": [120, 140, 130, 150, 145, 160, 155, 170, 165, 180, 175, 190],
            },
            xlabel="月",
            ylabel="金額（百万円）",
            title="月次推移"
        )

        # セグメント構成比（円グラフ）
        self.segment_chart.plot(
            labels=["製造事業", "流通事業", "サービス事業"],
            values=[45, 35, 20],
            title="セグメント構成比"
        )

        # 前年同月比較（棒グラフ）
        self.comparison_chart.plot(
            labels=["4月", "5月", "6月", "7月", "8月", "9月"],
            values=[105, 98, 112, 108, 95, 115],
            xlabel="月",
            ylabel="前年比（%）",
            title="前年同月比"
        )

        # 予備（折れ線グラフ）
        self.extra_chart.plot(
            x_data=list(range(1, 13)),
            y_data_dict={
                "売上高": [100, 105, 110, 108, 115, 120, 118, 125, 130, 128, 135, 140],
            },
            xlabel="月",
            ylabel="金額",
            title="売上推移"
        )

    def update_charts(self, years: list, segments: list, account: str):
        """
        グラフを更新

        Args:
            years: 選択された年度リスト
            segments: 選択されたセグメントリスト
            account: 選択された科目
        """
        # Phase 2-2-B以降で実際のデータ連携を実装
        print(f"グラフ更新: years={years}, segments={segments}, account={account}")
