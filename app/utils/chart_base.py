"""
matplotlib埋め込み基盤 - CustomTkinterにグラフを埋め込むための基底クラス
"""

import platform
from typing import Optional, Tuple

import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import customtkinter as ctk


def setup_japanese_font():
    """日本語フォントを設定"""
    system = platform.system()

    if system == "Windows":
        # Windows: MS Gothic または Meiryo
        font_candidates = ["MS Gothic", "Meiryo", "Yu Gothic"]
    elif system == "Darwin":
        # macOS: Hiragino
        font_candidates = ["Hiragino Sans", "Hiragino Kaku Gothic ProN"]
    else:
        # Linux: IPAexGothic
        font_candidates = ["IPAexGothic", "IPAGothic", "Noto Sans CJK JP"]

    # 利用可能なフォントを探す
    import matplotlib.font_manager as fm
    available_fonts = [f.name for f in fm.fontManager.ttflist]

    for font in font_candidates:
        if font in available_fonts:
            plt.rcParams["font.family"] = font
            break
    else:
        # フォールバック: sans-serif
        plt.rcParams["font.family"] = "sans-serif"

    # マイナス記号の文字化け対策
    plt.rcParams["axes.unicode_minus"] = False


# モジュール読み込み時にフォント設定
setup_japanese_font()


class ChartFrame(ctk.CTkFrame):
    """matplotlibグラフを埋め込むためのフレーム基底クラス"""

    def __init__(
        self,
        parent,
        figsize: Tuple[float, float] = (5, 4),
        dpi: int = 100,
        **kwargs
    ):
        """
        グラフフレームを初期化

        Args:
            parent: 親ウィジェット
            figsize: Figure サイズ (width, height) インチ単位
            dpi: 解像度
        """
        super().__init__(parent, **kwargs)

        self.figsize = figsize
        self.dpi = dpi

        # Figureとキャンバスを作成
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.ax = None

        self._create_chart()

    def _create_chart(self):
        """グラフの初期化"""
        # Figureを作成
        self.figure = Figure(figsize=self.figsize, dpi=self.dpi)
        self.figure.patch.set_facecolor("#f0f0f0")

        # Axesを作成
        self.ax = self.figure.add_subplot(111)

        # キャンバスを作成してフレームに配置
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def clear(self):
        """グラフをクリア"""
        if self.ax:
            self.ax.clear()

    def redraw(self):
        """グラフを再描画"""
        if self.canvas:
            self.figure.tight_layout()
            self.canvas.draw()

    def set_title(self, title: str):
        """グラフタイトルを設定"""
        if self.ax:
            self.ax.set_title(title, fontsize=12)

    def destroy(self):
        """リソースを解放"""
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.figure:
            plt.close(self.figure)
        super().destroy()


class LineChartFrame(ChartFrame):
    """折れ線グラフ用フレーム"""

    def plot(
        self,
        x_data: list,
        y_data_dict: dict,
        xlabel: str = "",
        ylabel: str = "",
        title: str = ""
    ):
        """
        折れ線グラフを描画

        Args:
            x_data: X軸データ
            y_data_dict: {ラベル: Y軸データ} の辞書
            xlabel: X軸ラベル
            ylabel: Y軸ラベル
            title: グラフタイトル
        """
        self.clear()

        for label, y_data in y_data_dict.items():
            self.ax.plot(x_data, y_data, marker="o", label=label)

        if xlabel:
            self.ax.set_xlabel(xlabel)
        if ylabel:
            self.ax.set_ylabel(ylabel)
        if title:
            self.set_title(title)

        if y_data_dict:
            self.ax.legend()

        self.ax.grid(True, alpha=0.3)
        self.redraw()


class BarChartFrame(ChartFrame):
    """棒グラフ用フレーム"""

    def plot(
        self,
        labels: list,
        values: list,
        xlabel: str = "",
        ylabel: str = "",
        title: str = "",
        horizontal: bool = False
    ):
        """
        棒グラフを描画

        Args:
            labels: ラベルリスト
            values: 値リスト
            xlabel: X軸ラベル
            ylabel: Y軸ラベル
            title: グラフタイトル
            horizontal: 横棒グラフにするか
        """
        self.clear()

        if horizontal:
            self.ax.barh(labels, values)
        else:
            self.ax.bar(labels, values)

        if xlabel:
            self.ax.set_xlabel(xlabel)
        if ylabel:
            self.ax.set_ylabel(ylabel)
        if title:
            self.set_title(title)

        self.redraw()


class PieChartFrame(ChartFrame):
    """円グラフ用フレーム"""

    def plot(
        self,
        labels: list,
        values: list,
        title: str = ""
    ):
        """
        円グラフを描画

        Args:
            labels: ラベルリスト
            values: 値リスト
            title: グラフタイトル
        """
        self.clear()

        # 負の値をフィルタリング（円グラフは正の値のみ対応）
        filtered_labels = []
        filtered_values = []
        has_negative = False

        for label, value in zip(labels, values):
            if value > 0:
                filtered_labels.append(label)
                filtered_values.append(value)
            elif value < 0:
                has_negative = True

        # 有効なデータがない場合
        if not filtered_values:
            self.ax.text(
                0.5, 0.5,
                "表示可能なデータがありません\n（負の値のみ）" if has_negative else "データがありません",
                ha="center", va="center", fontsize=12
            )
            if title:
                self.set_title(title)
            self.redraw()
            return

        self.ax.pie(
            filtered_values,
            labels=filtered_labels,
            autopct="%1.1f%%",
            startangle=90
        )
        self.ax.axis("equal")

        if title:
            # 負の値があった場合は注記を追加
            if has_negative:
                title += "\n（正の値のみ表示）"
            self.set_title(title)

        self.redraw()
