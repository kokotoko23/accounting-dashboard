"""
タブビュー - メインエリアのタブ構造
"""

from typing import Callable, List, Optional

import customtkinter as ctk

from app.models.database import AccountingDatabase
from app.views.dashboard_tab import DashboardTab
from app.views.customer_tab import CustomerTab
from app.views.segment_tab import SegmentTab


class MainTabView(ctk.CTkTabview):
    """メインエリアのタブビューコンポーネント"""

    TAB_DASHBOARD = "ダッシュボード"
    TAB_CUSTOMER = "取引先分析"
    TAB_SEGMENT = "セグメント分析"

    def __init__(
        self,
        parent,
        db: Optional[AccountingDatabase] = None,
        on_tab_change: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        """
        タブビューを初期化

        Args:
            parent: 親ウィジェット
            db: データベース接続
            on_tab_change: タブ変更時のコールバック関数
        """
        super().__init__(parent, **kwargs)

        self.db = db
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
        self.dashboard_tab = DashboardTab(self.dashboard_frame, db=self.db)
        self.dashboard_tab.pack(fill="both", expand=True)

    def update_dashboard(
        self,
        years: List[int],
        segments: List[str],
        account: str
    ):
        """
        ダッシュボードのグラフを更新

        Args:
            years: 選択された年度リスト
            segments: 選択されたセグメントリスト
            account: 選択された科目
        """
        if hasattr(self, "dashboard_tab"):
            self.dashboard_tab.update_charts(years, segments, account)

    def _create_customer_content(self):
        """取引先分析タブの内容を作成"""
        self.customer_tab = CustomerTab(self.customer_frame, db=self.db)
        self.customer_tab.pack(fill="both", expand=True)

    def update_customer(
        self,
        years: List[int],
        segments: List[str],
        account: str
    ):
        """
        取引先分析タブを更新

        Args:
            years: 選択された年度リスト
            segments: 選択されたセグメントリスト
            account: 選択された科目
        """
        if hasattr(self, "customer_tab"):
            self.customer_tab.update_data(years, segments, account)

    def _create_segment_content(self):
        """セグメント分析タブの内容を作成"""
        self.segment_tab = SegmentTab(self.segment_frame, db=self.db)
        self.segment_tab.pack(fill="both", expand=True)

    def update_segment(
        self,
        years: List[int],
        segments: List[str],
        account: str
    ):
        """
        セグメント分析タブを更新

        Args:
            years: 選択された年度リスト
            segments: 選択されたセグメントリスト
            account: 選択された科目
        """
        if hasattr(self, "segment_tab"):
            self.segment_tab.update_data(years, segments, account)

    def _on_tab_changed(self):
        """タブ変更時の処理"""
        current_tab = self.get()
        print(f"タブ切り替え: {current_tab}")

        if self.on_tab_change:
            self.on_tab_change(current_tab)

    def get_current_tab(self) -> str:
        """現在選択中のタブ名を取得"""
        return self.get()
