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
from app.utils.importer import CSVImporter
from app.views.import_dialog import ImportDialog, ImportResultDialog
from app.views.tab_view import MainTabView


class AccountingDashboardApp(ctk.CTk):
    """メインアプリケーションクラス"""

    def __init__(self):
        super().__init__()

        # ウィンドウ設定
        self.title("会計データ可視化ダッシュボード")
        self.geometry("1400x850")

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
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # ツールバー用
        self.grid_rowconfigure(1, weight=1)  # メイン領域
        self.grid_rowconfigure(2, weight=0)  # ステータスバー用

        # ツールバー
        self._create_toolbar()

        # メインエリア（タブビュー）
        self._create_main_area()

    def _create_toolbar(self):
        """ツールバーを作成"""
        self.toolbar = ctk.CTkFrame(self, height=40, corner_radius=0)
        self.toolbar.grid(row=0, column=0, sticky="ew")

        # インポートボタン
        self.import_btn = ctk.CTkButton(
            self.toolbar,
            text="CSVインポート",
            width=140,
            command=self._on_import_click
        )
        self.import_btn.pack(side="left", padx=10, pady=5)

        # エクスポートボタン
        self.export_btn = ctk.CTkButton(
            self.toolbar,
            text="CSVエクスポート",
            width=140,
            command=self._on_export_click
        )
        self.export_btn.pack(side="left", padx=5, pady=5)

    def _create_status_bar(self):
        """ステータスバーを作成"""
        self.status_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_frame.grid(row=2, column=0, sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="準備完了",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10, pady=5)

    def _create_main_area(self):
        """メインエリアを作成"""
        # タブビューを作成（データベース接続とステータス更新関数を渡す）
        self.tab_view = MainTabView(
            self,
            db=self.db,
            set_status=self._set_status
        )
        self.tab_view.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    def _on_import_click(self):
        """インポートボタンクリック時の処理"""
        # ファイル選択ダイアログを表示
        filepath = filedialog.askopenfilename(
            filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")],
            title="CSVインポート"
        )

        if not filepath:
            return  # キャンセルされた場合

        # インポートダイアログを表示
        dialog = ImportDialog(
            self,
            filepath=filepath,
            on_import=self._execute_import
        )
        self.wait_window(dialog)

    def _execute_import(self, filepath: str, mode: str):
        """
        インポートを実行

        Args:
            filepath: CSVファイルパス
            mode: "append" または "replace"
        """
        self._set_status("インポート中...", "normal")
        self.update_idletasks()

        try:
            importer = CSVImporter(self.db)
            success, count, errors = importer.import_csv(filepath, mode)

            # 結果ダイアログを表示
            result_dialog = ImportResultDialog(
                self,
                success=success,
                count=count,
                errors=errors
            )
            self.wait_window(result_dialog)

            if success:
                self._set_status(f"インポート完了: {count}件", "normal")
                # 各タブのフィルタを更新
                self.tab_view.refresh_all_filters()
            else:
                self._set_status("インポート失敗", "error")

        except Exception as e:
            error_msg = f"インポートエラー: {str(e)}"
            self._set_status(error_msg, "error")
            print(f"CSVインポートエラー: {e}")

    def _on_export_click(self):
        """エクスポートボタンクリック時の処理"""
        # 現在のタブからフィルタ値を取得
        filter_values = self.tab_view.get_current_filter_values()

        if not filter_values:
            self._set_status("エクスポートできるデータがありません", "error")
            return

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
                years=filter_values.get("years", []),
                divisions=filter_values.get("divisions", []),
                account=filter_values.get("account", "売上高")
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
        width = 1400
        height = 850
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
