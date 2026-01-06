"""
タブビュー - メインエリアのタブ構造
"""

from typing import Callable, Optional

import customtkinter as ctk

from app.views.dashboard_tab import DashboardTab


class MainTabView(ctk.CTkTabview):
    """メインエリアのタブビューコンポーネント"""

    TAB_DASHBOARD = "ダッシュボード"
    TAB_CUSTOMER = "取引先分析"
    TAB_SEGMENT = "セグメント分析"

    def __init__(
        self,
        parent,
        on_tab_change: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        """
        タブビューを初期化

        Args:
            parent: 親ウィジェット
            on_tab_change: タブ変更時のコールバック関数
        """
        super().__init__(parent, **kwargs)

        self.on_tab_change = on_tab_change

        # タブを作成
        self._create_tabs()

        # タブ変更イベントを設定
        self.configure(command=self._on_tab_changed)

    def _create_tabs(self):
        """タブを作成"""
        # ダッシュボードタブ
        self.add(self.TAB_DASHBOARD)
        self.dashboard_frame = self.tab(self.TAB_DASHBOARD)
        self._create_dashboard_content()

        # 取引先分析タブ
        self.add(self.TAB_CUSTOMER)
        self.customer_frame = self.tab(self.TAB_CUSTOMER)
        self._create_customer_content()

        # セグメント分析タブ
        self.add(self.TAB_SEGMENT)
        self.segment_frame = self.tab(self.TAB_SEGMENT)
        self._create_segment_content()

        # デフォルトはダッシュボードタブ
        self.set(self.TAB_DASHBOARD)

    def _create_dashboard_content(self):
        """ダッシュボードタブの内容を作成"""
        # ダッシュボードタブコンポーネントを作成
        self.dashboard_tab = DashboardTab(self.dashboard_frame)
        self.dashboard_tab.pack(fill="both", expand=True)

    def _create_customer_content(self):
        """取引先分析タブの内容を作成"""
        # プレースホルダー（Phase 2-4-Bで実装）
        label = ctk.CTkLabel(
            self.customer_frame,
            text="取引先分析\n（Phase 2-4-Bで実装）",
            font=ctk.CTkFont(size=18)
        )
        label.pack(expand=True)

    def _create_segment_content(self):
        """セグメント分析タブの内容を作成"""
        # プレースホルダー
        label = ctk.CTkLabel(
            self.segment_frame,
            text="セグメント分析\n（後で実装）",
            font=ctk.CTkFont(size=18)
        )
        label.pack(expand=True)

    def _on_tab_changed(self):
        """タブ変更時の処理"""
        current_tab = self.get()
        print(f"タブ切り替え: {current_tab}")

        if self.on_tab_change:
            self.on_tab_change(current_tab)

    def get_current_tab(self) -> str:
        """現在選択中のタブ名を取得"""
        return self.get()
