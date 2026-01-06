"""
フィルタパネル - 左サイドバーのフィルタUI
"""

from typing import Callable, Dict, List, Optional

import customtkinter as ctk


class FilterPanel(ctk.CTkFrame):
    """フィルタパネルコンポーネント"""

    def __init__(
        self,
        parent,
        years: List[int],
        segments: List[str],
        accounts: List[str],
        on_filter_change: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        """
        フィルタパネルを初期化

        Args:
            parent: 親ウィジェット
            years: 年度リスト
            segments: セグメントリスト
            accounts: 科目リスト
            on_filter_change: フィルタ変更時のコールバック関数
        """
        super().__init__(parent, **kwargs)

        self.years = years
        self.segments = segments
        self.accounts = accounts
        self.on_filter_change = on_filter_change

        # チェックボックスの状態を保持する変数
        self.year_vars: Dict[int, ctk.BooleanVar] = {}
        self.segment_vars: Dict[str, ctk.BooleanVar] = {}
        self.account_var = ctk.StringVar(value="売上高")

        self._create_widgets()

    def _create_widgets(self):
        """ウィジェットを作成"""
        # パネルタイトル
        title_label = ctk.CTkLabel(
            self,
            text="フィルタ",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(15, 20), padx=15, anchor="w")

        # 年度選択セクション
        self._create_year_section()

        # セグメント選択セクション
        self._create_segment_section()

        # 科目選択セクション
        self._create_account_section()

    def _create_year_section(self):
        """年度選択セクションを作成"""
        # セクションラベル
        year_label = ctk.CTkLabel(
            self,
            text="年度",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        year_label.pack(pady=(10, 5), padx=15, anchor="w")

        # 年度フレーム
        year_frame = ctk.CTkFrame(self, fg_color="transparent")
        year_frame.pack(fill="x", padx=15)

        # 全選択/解除ボタン
        btn_frame = ctk.CTkFrame(year_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 5))

        select_all_btn = ctk.CTkButton(
            btn_frame,
            text="全選択",
            width=60,
            height=24,
            font=ctk.CTkFont(size=11),
            command=lambda: self._select_all_years(True)
        )
        select_all_btn.pack(side="left", padx=(0, 5))

        deselect_all_btn = ctk.CTkButton(
            btn_frame,
            text="全解除",
            width=60,
            height=24,
            font=ctk.CTkFont(size=11),
            command=lambda: self._select_all_years(False)
        )
        deselect_all_btn.pack(side="left")

        # 年度チェックボックス
        for year in self.years:
            var = ctk.BooleanVar(value=True)  # デフォルトは全選択
            self.year_vars[year] = var

            cb = ctk.CTkCheckBox(
                year_frame,
                text=f"{year}年度",
                variable=var,
                command=self._on_filter_changed,
                font=ctk.CTkFont(size=13)
            )
            cb.pack(anchor="w", pady=2)

    def _create_segment_section(self):
        """セグメント選択セクションを作成"""
        # セクションラベル
        segment_label = ctk.CTkLabel(
            self,
            text="セグメント",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        segment_label.pack(pady=(20, 5), padx=15, anchor="w")

        # セグメントフレーム
        segment_frame = ctk.CTkFrame(self, fg_color="transparent")
        segment_frame.pack(fill="x", padx=15)

        # 全選択/解除ボタン
        btn_frame = ctk.CTkFrame(segment_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 5))

        select_all_btn = ctk.CTkButton(
            btn_frame,
            text="全選択",
            width=60,
            height=24,
            font=ctk.CTkFont(size=11),
            command=lambda: self._select_all_segments(True)
        )
        select_all_btn.pack(side="left", padx=(0, 5))

        deselect_all_btn = ctk.CTkButton(
            btn_frame,
            text="全解除",
            width=60,
            height=24,
            font=ctk.CTkFont(size=11),
            command=lambda: self._select_all_segments(False)
        )
        deselect_all_btn.pack(side="left")

        # セグメントチェックボックス
        for segment in self.segments:
            var = ctk.BooleanVar(value=True)  # デフォルトは全選択
            self.segment_vars[segment] = var

            cb = ctk.CTkCheckBox(
                segment_frame,
                text=segment,
                variable=var,
                command=self._on_filter_changed,
                font=ctk.CTkFont(size=13)
            )
            cb.pack(anchor="w", pady=2)

    def _create_account_section(self):
        """科目選択セクションを作成"""
        # セクションラベル
        account_label = ctk.CTkLabel(
            self,
            text="科目",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        account_label.pack(pady=(20, 5), padx=15, anchor="w")

        # デフォルト値を「売上高」に設定（リストに存在する場合）
        default_account = "売上高" if "売上高" in self.accounts else self.accounts[0]
        self.account_var.set(default_account)

        # 科目ドロップダウン
        account_dropdown = ctk.CTkOptionMenu(
            self,
            variable=self.account_var,
            values=self.accounts,
            command=lambda _: self._on_filter_changed(),
            font=ctk.CTkFont(size=13),
            width=180
        )
        account_dropdown.pack(padx=15, anchor="w")

    def _select_all_years(self, select: bool):
        """全年度を選択/解除"""
        for var in self.year_vars.values():
            var.set(select)
        self._on_filter_changed()

    def _select_all_segments(self, select: bool):
        """全セグメントを選択/解除"""
        for var in self.segment_vars.values():
            var.set(select)
        self._on_filter_changed()

    def _on_filter_changed(self):
        """フィルタ変更時の処理"""
        if self.on_filter_change:
            self.on_filter_change()

    def get_selected_years(self) -> List[int]:
        """選択中の年度リストを取得"""
        return [year for year, var in self.year_vars.items() if var.get()]

    def get_selected_segments(self) -> List[str]:
        """選択中のセグメントリストを取得"""
        return [seg for seg, var in self.segment_vars.items() if var.get()]

    def get_selected_account(self) -> str:
        """選択中の科目を取得"""
        return self.account_var.get()

    def get_filter_values(self) -> Dict:
        """現在のフィルタ値を辞書で取得"""
        return {
            "years": self.get_selected_years(),
            "segments": self.get_selected_segments(),
            "account": self.get_selected_account()
        }
