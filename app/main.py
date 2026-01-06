"""
会計データ可視化ダッシュボード - エントリーポイント
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加（直接実行時用）
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tkinter import filedialog

import customtkinter as ctk

from app.models.database import AccountingDatabase
from app.utils.exporter import CSVExporter
from app.views.filter_panel import FilterPanel
from app.views.tab_view import MainTabView


class AccountingDashboardApp(ctk.CTk):
    """メインアプリケーションクラス"""

    def __init__(self):
        super().__init__()

        # ウィンドウ設定
        self.title("会計データ可視化ダッシュボード")
        self.geometry("1280x800")

        # 外観設定
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # データベース接続
        self.db = AccountingDatabase()

        # UIを構築
        self._create_layout()

        # ステータスバーを作成
        self._create_status_bar()

        # ウィンドウを中央に配置
        self._center_window()

        # 終了時にデータベース接続を閉じる
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_layout(self):
        """レイアウトを作成"""
        # グリッド設定（ツールバー + メイン領域 + ステータスバー）
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)  # ツールバー用
        self.grid_rowconfigure(1, weight=1)  # メイン領域
        self.grid_rowconfigure(2, weight=0)  # ステータスバー用

        # ツールバー
        self._create_toolbar()

        # 左サイドバー（フィルタパネル）
        self._create_filter_panel()

        # メインエリア
        self._create_main_area()

    def _create_toolbar(self):
        """ツールバーを作成"""
        self.toolbar = ctk.CTkFrame(self, height=40, corner_radius=0)
        self.toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")

        # エクスポートボタン
        self.export_btn = ctk.CTkButton(
            self.toolbar,
            text="📥 CSVエクスポート",
            width=140,
            command=self._on_export_click
        )
        self.export_btn.pack(side="left", padx=10, pady=5)

    def _create_status_bar(self):
        """ステータスバーを作成"""
        self.status_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="準備完了",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10, pady=5)

    def _create_filter_panel(self):
        """フィルタパネルを作成"""
        # データベースからフィルタ用データを取得
        years = self.db.get_years()
        segments = self.db.get_segments()
        accounts = self.db.get_accounts()

        # フィルタパネルを作成
        self.filter_panel = FilterPanel(
            self,
            years=years,
            segments=segments,
            accounts=accounts,
            on_filter_change=self._on_filter_change,
            width=220
        )
        self.filter_panel.grid(row=1, column=0, sticky="nsw", padx=0, pady=0)

    def _create_main_area(self):
        """メインエリアを作成"""
        # タブビューを作成（データベース接続を渡す）
        self.tab_view = MainTabView(
            self,
            db=self.db,
            on_tab_change=self._on_tab_change
        )
        self.tab_view.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        # 初期データでグラフを表示
        self._update_dashboard()

    def _on_tab_change(self, tab_name: str):
        """タブ変更時のコールバック"""
        # タブ切り替え時にデータを更新
        if tab_name == MainTabView.TAB_DASHBOARD:
            self._update_dashboard()
        elif tab_name == MainTabView.TAB_CUSTOMER:
            self._update_customer()

    def _on_filter_change(self):
        """フィルタ変更時のコールバック"""
        filter_values = self.filter_panel.get_filter_values()
        print(f"フィルタ変更: {filter_values}")

        # 現在のタブに応じてデータを更新
        current_tab = self.tab_view.get_current_tab()
        if current_tab == MainTabView.TAB_DASHBOARD:
            self._update_dashboard()
        elif current_tab == MainTabView.TAB_CUSTOMER:
            self._update_customer()

    def _update_dashboard(self):
        """ダッシュボードのグラフを更新"""
        filter_values = self.filter_panel.get_filter_values()

        # ローディング表示
        self._set_status("グラフを更新中...", "normal")
        self.update_idletasks()

        try:
            self.tab_view.update_dashboard(
                years=filter_values["years"],
                segments=filter_values["segments"],
                account=filter_values["account"]
            )
            self._set_status("更新完了", "normal")
        except Exception as e:
            error_msg = f"エラー: {str(e)}"
            self._set_status(error_msg, "error")
            print(f"グラフ更新エラー: {e}")

    def _update_customer(self):
        """取引先分析タブを更新"""
        filter_values = self.filter_panel.get_filter_values()

        # ローディング表示
        self._set_status("取引先データを更新中...", "normal")
        self.update_idletasks()

        try:
            self.tab_view.update_customer(
                years=filter_values["years"],
                segments=filter_values["segments"],
                account=filter_values["account"]
            )
            self._set_status("更新完了", "normal")
        except Exception as e:
            error_msg = f"エラー: {str(e)}"
            self._set_status(error_msg, "error")
            print(f"取引先データ更新エラー: {e}")

    def _on_export_click(self):
        """エクスポートボタンクリック時の処理"""
        filter_values = self.filter_panel.get_filter_values()

        # デフォルトファイル名を生成
        default_filename = CSVExporter.get_default_filename()

        # ファイル保存ダイアログを表示
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")],
            initialfile=default_filename,
            title="CSVエクスポート"
        )

        if not filepath:
            return  # キャンセルされた場合

        self._set_status("エクスポート中...", "normal")
        self.update_idletasks()

        try:
            exporter = CSVExporter(self.db)
            success = exporter.export_all_data(
                filepath=filepath,
                years=filter_values["years"],
                segments=filter_values["segments"],
                account=filter_values["account"]
            )

            if success:
                self._set_status(f"エクスポート完了: {filepath}", "normal")
            else:
                self._set_status("エクスポートするデータがありません", "error")

        except Exception as e:
            error_msg = f"エクスポートエラー: {str(e)}"
            self._set_status(error_msg, "error")
            print(f"CSVエクスポートエラー: {e}")

    def _set_status(self, message: str, status_type: str = "normal"):
        """
        ステータスバーのメッセージを設定

        Args:
            message: 表示するメッセージ
            status_type: "normal" または "error"
        """
        if hasattr(self, "status_label"):
            self.status_label.configure(text=message)
            if status_type == "error":
                self.status_label.configure(text_color="red")
            else:
                self.status_label.configure(text_color=("gray10", "gray90"))

    def _center_window(self):
        """ウィンドウを画面中央に配置"""
        self.update_idletasks()
        width = 1280
        height = 800
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _on_closing(self):
        """ウィンドウ終了時の処理"""
        self.db.close()
        self.destroy()


def main():
    """アプリケーション起動"""
    app = AccountingDashboardApp()
    app.mainloop()


if __name__ == "__main__":
    main()
