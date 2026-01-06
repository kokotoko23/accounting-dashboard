"""
会計データ可視化ダッシュボード - エントリーポイント
"""

import customtkinter as ctk

from app.models.database import AccountingDatabase
from app.views.filter_panel import FilterPanel


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

        # ウィンドウを中央に配置
        self._center_window()

        # 終了時にデータベース接続を閉じる
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_layout(self):
        """レイアウトを作成"""
        # グリッド設定
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 左サイドバー（フィルタパネル）
        self._create_filter_panel()

        # メインエリア（後でタブ構造を追加）
        self._create_main_area()

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
        self.filter_panel.grid(row=0, column=0, sticky="nsw", padx=0, pady=0)

    def _create_main_area(self):
        """メインエリアを作成"""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # プレースホルダーラベル（後でタブ構造に置き換え）
        placeholder = ctk.CTkLabel(
            self.main_frame,
            text="メインエリア\n（Phase 2-1-Cでタブ構造を実装）",
            font=ctk.CTkFont(size=16)
        )
        placeholder.pack(expand=True)

    def _on_filter_change(self):
        """フィルタ変更時のコールバック"""
        filter_values = self.filter_panel.get_filter_values()
        print(f"フィルタ変更: {filter_values}")

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
