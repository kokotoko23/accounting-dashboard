"""
サマリーパネル - ダッシュボード上部のKPIカード表示
"""

from typing import List, Optional

import customtkinter as ctk

from app.models.database import AccountingDatabase


class SummaryCard(ctk.CTkFrame):
    """サマリーカードコンポーネント"""

    def __init__(
        self,
        parent,
        title: str,
        value: str = "-",
        sub_value: str = "",
        sub_color: str = "gray",
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        # タイトル
        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.title_label.pack(pady=(10, 2))

        # メイン値
        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.value_label.pack(pady=2)

        # サブ値（前年比など）
        self.sub_label = ctk.CTkLabel(
            self,
            text=sub_value,
            font=ctk.CTkFont(size=12),
            text_color=sub_color
        )
        self.sub_label.pack(pady=(2, 10))

    def update_values(self, value: str, sub_value: str = "", sub_color: str = "gray"):
        """値を更新"""
        self.value_label.configure(text=value)
        self.sub_label.configure(text=sub_value, text_color=sub_color)


class SummaryPanel(ctk.CTkFrame):
    """サマリーパネルコンポーネント"""

    def __init__(
        self,
        parent,
        db: Optional[AccountingDatabase] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.db = db if db else AccountingDatabase()
        self._owns_db = db is None

        # カードを横並びに配置
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._create_cards()

    def _create_cards(self):
        """サマリーカードを作成"""
        # 合計金額カード
        self.total_card = SummaryCard(
            self,
            title="合計金額",
            value="¥0",
            corner_radius=10
        )
        self.total_card.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # 前年比カード
        self.yoy_card = SummaryCard(
            self,
            title="前年比",
            value="-",
            corner_radius=10
        )
        self.yoy_card.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # 取引先数カード
        self.customer_card = SummaryCard(
            self,
            title="取引先数",
            value="0社",
            corner_radius=10
        )
        self.customer_card.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        # 取引件数カード
        self.transaction_card = SummaryCard(
            self,
            title="取引件数",
            value="0件",
            corner_radius=10
        )
        self.transaction_card.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

    def update_summary(
        self,
        years: List[int],
        segments: List[str],
        account: str
    ):
        """サマリーを更新"""
        if not years or not segments:
            self._reset_cards()
            return

        try:
            # 合計金額を計算
            total = self._calculate_total(years, segments, account)
            self.total_card.update_values(self._format_currency(total))

            # 前年比を計算
            if len(years) >= 2:
                yoy = self._calculate_yoy(years, segments, account)
                yoy_text = f"{yoy:+.1f}%" if yoy is not None else "-"
                yoy_color = "green" if yoy and yoy >= 0 else "red"
                self.yoy_card.update_values(yoy_text, sub_color=yoy_color)
            else:
                self.yoy_card.update_values("-", "2年以上選択してください", "gray")

            # 取引先数を計算
            customer_count = self._count_customers(years, segments, account)
            self.customer_card.update_values(f"{customer_count:,}社")

            # 取引件数を計算
            transaction_count = self._count_transactions(years, segments, account)
            self.transaction_card.update_values(f"{transaction_count:,}件")

        except Exception as e:
            print(f"サマリー更新エラー: {e}")
            self._reset_cards()

    def _calculate_total(
        self,
        years: List[int],
        segments: List[str],
        account: str
    ) -> int:
        """合計金額を計算"""
        df = self.db.get_monthly_data(years, segments, account)
        if df.empty:
            return 0
        return int(df["total"].sum())

    def _calculate_yoy(
        self,
        years: List[int],
        segments: List[str],
        account: str
    ) -> Optional[float]:
        """前年比を計算"""
        sorted_years = sorted(years)
        current_year = sorted_years[-1]
        prev_year = sorted_years[-2]

        current_df = self.db.get_monthly_data([current_year], segments, account)
        prev_df = self.db.get_monthly_data([prev_year], segments, account)

        if current_df.empty or prev_df.empty:
            return None

        current_total = current_df["total"].sum()
        prev_total = prev_df["total"].sum()

        if prev_total == 0:
            return None

        return ((current_total - prev_total) / prev_total) * 100

    def _count_customers(
        self,
        years: List[int],
        segments: List[str],
        account: str
    ) -> int:
        """取引先数をカウント"""
        conn = self.db.connection

        placeholders_years = ",".join("?" * len(years))
        placeholders_segments = ",".join("?" * len(segments))

        query = f"""
            SELECT COUNT(DISTINCT customer_code) as count
            FROM transactions_denormalized
            WHERE account = ?
              AND year IN ({placeholders_years})
              AND segment IN ({placeholders_segments})
        """
        params = [account] + years + segments

        cursor = conn.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result else 0

    def _count_transactions(
        self,
        years: List[int],
        segments: List[str],
        account: str
    ) -> int:
        """取引件数をカウント"""
        conn = self.db.connection

        placeholders_years = ",".join("?" * len(years))
        placeholders_segments = ",".join("?" * len(segments))

        query = f"""
            SELECT COUNT(*) as count
            FROM transactions_denormalized
            WHERE account = ?
              AND year IN ({placeholders_years})
              AND segment IN ({placeholders_segments})
        """
        params = [account] + years + segments

        cursor = conn.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result else 0

    def _format_currency(self, amount: int) -> str:
        """金額をフォーマット"""
        return f"¥{amount:,}"

    def _reset_cards(self):
        """カードをリセット"""
        self.total_card.update_values("¥0")
        self.yoy_card.update_values("-")
        self.customer_card.update_values("0社")
        self.transaction_card.update_values("0件")

    def destroy(self):
        """リソースを解放"""
        if self._owns_db and self.db:
            self.db.close()
        super().destroy()
