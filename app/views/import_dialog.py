"""
CSVインポートダイアログ - インポート設定と結果表示
"""

from typing import Callable, Optional

import customtkinter as ctk


class ImportDialog(ctk.CTkToplevel):
    """CSVインポート設定ダイアログ"""

    def __init__(
        self,
        parent,
        filepath: str,
        on_import: Optional[Callable[[str, str], None]] = None,
        **kwargs
    ):
        """
        ダイアログを初期化

        Args:
            parent: 親ウィンドウ
            filepath: インポートするCSVファイルパス
            on_import: インポート実行時のコールバック (filepath, mode) -> None
        """
        super().__init__(parent, **kwargs)

        self.filepath = filepath
        self.on_import = on_import
        self.result = None

        # ウィンドウ設定
        self.title("CSVインポート")
        self.geometry("500x350")
        self.resizable(False, False)

        # モーダルにする
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._center_window(parent)

    def _create_widgets(self):
        """ウィジェットを作成"""
        # ファイルパス表示
        file_frame = ctk.CTkFrame(self)
        file_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            file_frame,
            text="インポートファイル:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # ファイル名を短縮表示
        filename = self.filepath
        if len(filename) > 50:
            filename = "..." + filename[-47:]

        ctk.CTkLabel(
            file_frame,
            text=filename,
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=10, pady=(0, 10))

        # インポートモード選択
        mode_frame = ctk.CTkFrame(self)
        mode_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            mode_frame,
            text="インポートモード:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self.mode_var = ctk.StringVar(value="append")

        ctk.CTkRadioButton(
            mode_frame,
            text="追加（既存データを保持）",
            variable=self.mode_var,
            value="append"
        ).pack(anchor="w", padx=20, pady=5)

        ctk.CTkRadioButton(
            mode_frame,
            text="置換（既存データを削除）",
            variable=self.mode_var,
            value="replace"
        ).pack(anchor="w", padx=20, pady=(5, 10))

        # 注意事項
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            info_frame,
            text="必須カラム:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        columns_text = "year, month, segment, division, dept_code, dept_name,\ncustomer_code, customer_name, industry, account, amount"
        ctk.CTkLabel(
            info_frame,
            text=columns_text,
            font=ctk.CTkFont(size=11),
            justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 5))

        ctk.CTkLabel(
            info_frame,
            text="※ 日本語カラム名（年度、月、セグメント等）も対応",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", padx=10, pady=(0, 10))

        # ボタン
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(
            button_frame,
            text="キャンセル",
            width=100,
            fg_color="gray",
            command=self._on_cancel
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            button_frame,
            text="インポート",
            width=100,
            command=self._on_import
        ).pack(side="right", padx=5)

    def _center_window(self, parent):
        """親ウィンドウの中央に配置"""
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        width = 500
        height = 350
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.geometry(f"{width}x{height}+{x}+{y}")

    def _on_import(self):
        """インポートボタン押下時"""
        self.result = {
            "filepath": self.filepath,
            "mode": self.mode_var.get()
        }
        if self.on_import:
            self.on_import(self.filepath, self.mode_var.get())
        self.destroy()

    def _on_cancel(self):
        """キャンセルボタン押下時"""
        self.result = None
        self.destroy()


class ImportResultDialog(ctk.CTkToplevel):
    """インポート結果表示ダイアログ"""

    def __init__(
        self,
        parent,
        success: bool,
        count: int,
        errors: list,
        **kwargs
    ):
        """
        ダイアログを初期化

        Args:
            parent: 親ウィンドウ
            success: 成功フラグ
            count: インポート件数
            errors: エラーリスト
        """
        super().__init__(parent, **kwargs)

        self.success = success
        self.count = count
        self.errors = errors

        # ウィンドウ設定
        self.title("インポート結果")
        self.geometry("450x300")
        self.resizable(False, False)

        # モーダルにする
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._center_window(parent)

    def _create_widgets(self):
        """ウィジェットを作成"""
        # 結果アイコンとメッセージ
        if self.success:
            icon = "✅"
            message = f"インポートが完了しました"
            detail = f"{self.count:,} 件のデータをインポートしました"
            color = "green"
        else:
            icon = "❌"
            message = "インポートに失敗しました"
            detail = "エラー内容を確認してください"
            color = "red"

        # アイコン
        ctk.CTkLabel(
            self,
            text=icon,
            font=ctk.CTkFont(size=48)
        ).pack(pady=(30, 10))

        # メッセージ
        ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=color
        ).pack(pady=5)

        # 詳細
        ctk.CTkLabel(
            self,
            text=detail,
            font=ctk.CTkFont(size=12)
        ).pack(pady=5)

        # エラー表示
        if self.errors:
            error_frame = ctk.CTkFrame(self)
            error_frame.pack(fill="both", expand=True, padx=20, pady=10)

            ctk.CTkLabel(
                error_frame,
                text="詳細:",
                font=ctk.CTkFont(weight="bold")
            ).pack(anchor="w", padx=10, pady=(10, 5))

            error_text = "\n".join(self.errors[:10])
            if len(self.errors) > 10:
                error_text += f"\n...他 {len(self.errors) - 10} 件"

            error_label = ctk.CTkLabel(
                error_frame,
                text=error_text,
                font=ctk.CTkFont(size=11),
                justify="left",
                wraplength=380
            )
            error_label.pack(anchor="w", padx=10, pady=(0, 10))

        # OKボタン
        ctk.CTkButton(
            self,
            text="OK",
            width=100,
            command=self.destroy
        ).pack(pady=20)

    def _center_window(self, parent):
        """親ウィンドウの中央に配置"""
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        width = 450
        height = 300
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.geometry(f"{width}x{height}+{x}+{y}")
