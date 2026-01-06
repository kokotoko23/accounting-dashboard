"""
セグメント分析タブ - セグメント別比較と推移分析
"""

from typing import List, Optional, Callable

import customtkinter as ctk
from tkinter import ttk

from app.models.database import AccountingDatabase
from app.utils.chart_base import BarChartFrame, LineChartFrame, PieChartFrame


class SegmentComparisonTable(ctk.CTkFrame):
    """セグメント比較テーブル"""

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
            text="セグメント別実績",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        header.pack(pady=(10, 5), anchor="w", padx=10)

        # Treeview作成
        columns = ("segment", "current", "prev", "yoy", "share")
        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=10
        )

        # 列の設定
        self.tree.heading("segment", text="セグメント")
        self.tree.heading("current", text="当期")
        self.tree.heading("prev", text="前期")
        self.tree.heading("yoy", text="前年比")
        self.tree.heading("share", text="構成比")

        self.tree.column("segment", width=150)
        self.tree.column("current", width=120, anchor="e")
        self.tree.column("prev", width=120, anchor="e")
        self.tree.column("yoy", width=80, anchor="center")
        self.tree.column("share", width=80, anchor="center")

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
                segment_name = values[0]
                self.on_select(segment_name)

    def update_data(self, data: list):
        """
        データを更新

        Args:
            data: [(セグメント, 当期, 前期, 前年比, 構成比), ...] のリスト
        """
        # 既存データをクリア
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 新しいデータを挿入
        for row in data:
            self.tree.insert("", "end", values=row)


class SegmentTab(ctk.CTkFrame):
    """セグメント分析タブコンポーネント"""

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
        self.current_segments: List[str] = []
        self.current_account: str = "売上高"
        self.selected_segment: Optional[str] = None

        # レイアウト設定
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_widgets()

    def _create_widgets(self):
        """ウィジェットを作成"""
        # 左上: セグメント比較テーブル
        self.comparison_table = SegmentComparisonTable(
            self,
            on_select=self._on_segment_select
        )
        self.comparison_table.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # 右上: セグメント別構成比（円グラフ）
        self.share_chart = PieChartFrame(
            self,
            figsize=(5, 3.5),
            dpi=100
        )
        self.share_chart.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # 左下: セグメント別比較（棒グラフ）
        self.comparison_chart = BarChartFrame(
            self,
            figsize=(5, 3.5),
            dpi=100
        )
        self.comparison_chart.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # 右下: 選択セグメントの月次推移
        self.trend_chart = LineChartFrame(
            self,
            figsize=(5, 3.5),
            dpi=100
        )
        self.trend_chart.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # 初期メッセージ
        self.trend_chart.ax.text(
            0.5, 0.5, "セグメントを選択してください",
            ha="center", va="center", fontsize=12
        )
        self.trend_chart.redraw()

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
        self.current_segments = segments
        self.current_account = account

        if not years:
            return

        # セグメント比較テーブルを更新
        self._update_comparison_table(years, account)

        # セグメント別構成比グラフを更新
        self._update_share_chart(years, account)

        # セグメント別比較グラフを更新
        self._update_comparison_chart(years, account)

        # 選択セグメントがあれば月次推移も更新
        if self.selected_segment:
            self._update_trend_chart(self.selected_segment)

    def _update_comparison_table(self, years: List[int], account: str):
        """セグメント比較テーブルを更新"""
        if not years:
            self.comparison_table.update_data([])
            return

        sorted_years = sorted(years)
        current_year = sorted_years[-1]
        prev_year = sorted_years[-2] if len(sorted_years) >= 2 else None

        # 当期のセグメント別集計
        df_current = self.db.get_segment_summary([current_year], account)

        if df_current.empty:
            self.comparison_table.update_data([])
            return

        # 前期のセグメント別集計
        df_prev = None
        if prev_year:
            df_prev = self.db.get_segment_summary([prev_year], account)

        # 合計を計算（構成比用）
        total_current = df_current["total"].sum()

        # テーブルデータを作成
        data = []
        for _, row in df_current.iterrows():
            segment = row["segment"]
            current_val = row["total"]

            # 前期値を取得
            prev_val = 0
            if df_prev is not None and not df_prev.empty:
                prev_row = df_prev[df_prev["segment"] == segment]
                if not prev_row.empty:
                    prev_val = prev_row["total"].values[0]

            # 前年比を計算
            if prev_val > 0:
                yoy = f"{(current_val / prev_val) * 100:.1f}%"
            else:
                yoy = "-"

            # 構成比を計算
            share = f"{(current_val / total_current) * 100:.1f}%" if total_current > 0 else "-"

            data.append((
                segment,
                f"¥{int(current_val):,}",
                f"¥{int(prev_val):,}" if prev_val > 0 else "-",
                yoy,
                share
            ))

        self.comparison_table.update_data(data)

    def _update_share_chart(self, years: List[int], account: str):
        """セグメント別構成比グラフを更新"""
        if not years:
            self.share_chart.clear()
            self.share_chart.set_title("セグメント構成比（データなし）")
            self.share_chart.redraw()
            return

        latest_year = max(years)
        df = self.db.get_segment_summary([latest_year], account)

        if df.empty:
            self.share_chart.clear()
            self.share_chart.set_title("セグメント構成比（データなし）")
            self.share_chart.redraw()
            return

        self.share_chart.plot(
            labels=df["segment"].tolist(),
            values=df["total"].tolist(),
            title=f"セグメント構成比 {latest_year}年度 - {account}"
        )

    def _update_comparison_chart(self, years: List[int], account: str):
        """セグメント別比較グラフを更新"""
        if not years or len(years) < 2:
            # 1年だけの場合は単純な棒グラフ
            if years:
                df = self.db.get_segment_summary(years, account)
                if not df.empty:
                    self.comparison_chart.plot(
                        labels=df["segment"].tolist(),
                        values=[v / 1_000_000 for v in df["total"].tolist()],
                        xlabel="セグメント",
                        ylabel="金額（百万円）",
                        title=f"セグメント別実績 {years[0]}年度 - {account}"
                    )
                    return

            self.comparison_chart.clear()
            self.comparison_chart.set_title("セグメント比較（2年以上選択してください）")
            self.comparison_chart.redraw()
            return

        # 複数年の比較用データを準備
        sorted_years = sorted(years)[-2:]  # 最新2年のみ
        current_year = sorted_years[-1]
        prev_year = sorted_years[-2]

        df_current = self.db.get_segment_summary([current_year], account)
        df_prev = self.db.get_segment_summary([prev_year], account)

        if df_current.empty:
            self.comparison_chart.clear()
            self.comparison_chart.set_title("セグメント比較（データなし）")
            self.comparison_chart.redraw()
            return

        # グラフ用データを作成
        segments = df_current["segment"].tolist()
        current_values = [v / 1_000_000 for v in df_current["total"].tolist()]

        prev_values = []
        for segment in segments:
            if not df_prev.empty:
                prev_row = df_prev[df_prev["segment"] == segment]
                if not prev_row.empty:
                    prev_values.append(prev_row["total"].values[0] / 1_000_000)
                else:
                    prev_values.append(0)
            else:
                prev_values.append(0)

        # 複数系列の棒グラフを描画
        self._plot_grouped_bar(
            segments,
            {f"{prev_year}年度": prev_values, f"{current_year}年度": current_values},
            f"セグメント別年度比較 - {account}"
        )

    def _plot_grouped_bar(self, labels: List[str], data_dict: dict, title: str):
        """グループ化された棒グラフを描画"""
        import numpy as np

        self.comparison_chart.clear()
        ax = self.comparison_chart.ax

        x = np.arange(len(labels))
        width = 0.35
        multiplier = 0

        colors = ["#90CAF9", "#1976D2"]  # 淡い青、濃い青

        for i, (label, values) in enumerate(data_dict.items()):
            offset = width * multiplier
            ax.bar(x + offset, values, width, label=label, color=colors[i % len(colors)])
            multiplier += 1

        ax.set_xlabel("セグメント")
        ax.set_ylabel("金額（百万円）")
        ax.set_title(title)
        ax.set_xticks(x + width / 2)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.legend(loc="upper right")
        ax.grid(axis="y", alpha=0.3)

        self.comparison_chart.fig.tight_layout()
        self.comparison_chart.redraw()

    def _on_segment_select(self, segment_name: str):
        """セグメント選択時の処理"""
        self.selected_segment = segment_name
        self._update_trend_chart(segment_name)

    def _update_trend_chart(self, segment_name: str):
        """選択セグメントの月次推移を更新"""
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
                WHERE segment = ?
                  AND account = ?
                  AND year = ?
                  AND month IN ({placeholders})
                GROUP BY month
                ORDER BY month
            """
            params = [segment_name, account, year] + months

            cursor = conn.execute(query, params)
            results = {row[0]: row[1] for row in cursor.fetchall()}

            monthly_values = [results.get(m, 0) / 1_000_000 for m in months]
            y_data_dict[f"{year}年度"] = monthly_values

        if not y_data_dict:
            self.trend_chart.clear()
            self.trend_chart.set_title("データなし")
            self.trend_chart.redraw()
            return

        self.trend_chart.plot(
            x_data=months,
            y_data_dict=y_data_dict,
            xlabel="月",
            ylabel="金額（百万円）",
            title=f"{segment_name} - {account}"
        )

    def destroy(self):
        """リソースを解放"""
        if self._owns_db and self.db:
            self.db.close()
        super().destroy()
