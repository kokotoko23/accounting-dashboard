"""
会計データ可視化ダッシュボード - エントリーポイント
"""

import customtkinter as ctk


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

        # ウィンドウを中央に配置
        self._center_window()

    def _center_window(self):
        """ウィンドウを画面中央に配置"""
        self.update_idletasks()
        width = 1280
        height = 800
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")


def main():
    """アプリケーション起動"""
    app = AccountingDashboardApp()
    app.mainloop()


if __name__ == "__main__":
    main()
