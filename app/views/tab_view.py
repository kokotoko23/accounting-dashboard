"""
タブビュー - メインエリアのタブ構造
"""

from typing import Callable, Dict, Optional

import customtkinter as ctk

from app.models.database import AccountingDatabase
from app.views.dashboard_tab import DashboardTab
from app.views.customer_tab import CustomerTab
from app.views.department_tab import DepartmentTab


class MainTabView(ctk.CTkTabview):
    """メインエリアのタブビューコンポーネント"""

    TAB_DASHBOARD = "ダッシュボード"
    TAB_DEPARTMENT = "部門分析"
    TAB_CUSTOMER = "取引先分析"

    def __init__(
        self,
        parent,
        db: Optional[AccountingDatabase] = None,
        set_status: Optional[Callable[[str, str], None]] = None,
        **kwargs
    ):
        """
        タブビューを初期化

        Args:
            parent: 親ウィジェット
            db: データベース接続
            set_status: ステータスバー更新関数
        """
        super().__init__(parent, **kwargs)

        self.db = db
        self.set_status = set_status

        # タブを作成
        self._create_tabs()

    def _create_tabs(self):
        """タブを作成"""
        # ダッシュボードタブ
        self.add(self.TAB_DASHBOARD)
        self.dashboard_frame = self.tab(self.TAB_DASHBOARD)
        self._create_dashboard_content()

        # 部門分析タブ
        self.add(self.TAB_DEPARTMENT)
        self.department_frame = self.tab(self.TAB_DEPARTMENT)
        self._create_department_content()

        # 取引先分析タブ
        self.add(self.TAB_CUSTOMER)
        self.customer_frame = self.tab(self.TAB_CUSTOMER)
        self._create_customer_content()

        # デフォルトはダッシュボードタブ
        self.set(self.TAB_DASHBOARD)

    def _create_dashboard_content(self):
        """ダッシュボードタブの内容を作成"""
        self.dashboard_tab = DashboardTab(
            self.dashboard_frame,
            db=self.db,
            set_status=self.set_status
        )
        self.dashboard_tab.pack(fill="both", expand=True)

    def _create_department_content(self):
        """部門分析タブの内容を作成"""
        self.department_tab = DepartmentTab(
            self.department_frame,
            db=self.db,
            set_status=self.set_status
        )
        self.department_tab.pack(fill="both", expand=True)

    def _create_customer_content(self):
        """取引先分析タブの内容を作成"""
        self.customer_tab = CustomerTab(
            self.customer_frame,
            db=self.db,
            set_status=self.set_status
        )
        self.customer_tab.pack(fill="both", expand=True)

    def refresh_all_filters(self):
        """全タブのフィルタを更新（データインポート後など）"""
        if hasattr(self, "dashboard_tab"):
            self.dashboard_tab.refresh_filters()
        if hasattr(self, "department_tab"):
            self.department_tab.refresh_filters()
        if hasattr(self, "customer_tab"):
            self.customer_tab.refresh_filters()

    def get_current_filter_values(self) -> Optional[Dict]:
        """現在のタブのフィルタ値を取得"""
        current_tab = self.get()

        if current_tab == self.TAB_DASHBOARD and hasattr(self, "dashboard_tab"):
            return self.dashboard_tab.get_filter_values()
        elif current_tab == self.TAB_DEPARTMENT and hasattr(self, "department_tab"):
            return self.department_tab.get_filter_values()
        elif current_tab == self.TAB_CUSTOMER and hasattr(self, "customer_tab"):
            return self.customer_tab.get_filter_values()

        return None

    def get_current_tab(self) -> str:
        """現在選択中のタブ名を取得"""
        return self.get()
