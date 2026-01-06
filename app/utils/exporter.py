"""
CSVエクスポート機能
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.models.database import AccountingDatabase


class CSVExporter:
    """CSVエクスポートクラス"""

    def __init__(self, db: Optional[AccountingDatabase] = None):
        self.db = db if db else AccountingDatabase()
        self._owns_db = db is None

    def export_monthly_data(
        self,
        filepath: str,
        years: List[int],
        segments: List[str],
        account: str
    ) -> bool:
        """
        月次データをCSVエクスポート

        Args:
            filepath: 出力ファイルパス
            years: 年度リスト
            segments: セグメントリスト
            account: 科目

        Returns:
            成功したかどうか
        """
        try:
            df = self.db.get_monthly_data(years, segments, account)

            if df.empty:
                return False

            # UTF-8 with BOM で出力（Excel対応）
            with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)

                # ヘッダー
                writer.writerow(["年度", "月", "金額", "科目"])

                # データ
                for _, row in df.iterrows():
                    writer.writerow([
                        row["year"],
                        row["month"],
                        row["total"],
                        account
                    ])

            return True

        except Exception as e:
            print(f"CSVエクスポートエラー: {e}")
            return False

    def export_segment_summary(
        self,
        filepath: str,
        years: List[int],
        account: str
    ) -> bool:
        """
        セグメント別集計をCSVエクスポート

        Args:
            filepath: 出力ファイルパス
            years: 年度リスト
            account: 科目

        Returns:
            成功したかどうか
        """
        try:
            df = self.db.get_segment_summary(years, account)

            if df.empty:
                return False

            # UTF-8 with BOM で出力
            with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)

                # ヘッダー
                writer.writerow(["セグメント", "金額", "科目", "対象年度"])

                # データ
                years_str = ",".join(str(y) for y in sorted(years))
                for _, row in df.iterrows():
                    writer.writerow([
                        row["segment"],
                        row["total"],
                        account,
                        years_str
                    ])

            return True

        except Exception as e:
            print(f"CSVエクスポートエラー: {e}")
            return False

    def export_customer_ranking(
        self,
        filepath: str,
        year: int,
        account: str,
        limit: int = 20
    ) -> bool:
        """
        取引先ランキングをCSVエクスポート

        Args:
            filepath: 出力ファイルパス
            year: 年度
            account: 科目
            limit: 出力件数

        Returns:
            成功したかどうか
        """
        try:
            df = self.db.get_customer_ranking(year, account, limit)

            if df.empty:
                return False

            # UTF-8 with BOM で出力
            with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)

                # ヘッダー
                writer.writerow(["順位", "取引先名", "業種", "金額", "年度", "科目"])

                # データ
                for i, (_, row) in enumerate(df.iterrows(), 1):
                    writer.writerow([
                        i,
                        row["customer_name"],
                        row["industry"],
                        row["total"],
                        year,
                        account
                    ])

            return True

        except Exception as e:
            print(f"CSVエクスポートエラー: {e}")
            return False

    def export_all_data(
        self,
        filepath: str,
        years: List[int],
        segments: List[str],
        account: str
    ) -> bool:
        """
        全データ（詳細）をCSVエクスポート

        Args:
            filepath: 出力ファイルパス
            years: 年度リスト
            segments: セグメントリスト
            account: 科目

        Returns:
            成功したかどうか
        """
        try:
            conn = self.db.connection

            placeholders_years = ",".join("?" * len(years))
            placeholders_segments = ",".join("?" * len(segments))

            query = f"""
                SELECT year, month, segment, division, dept_name,
                       customer_name, industry, account, amount
                FROM transactions_denormalized
                WHERE account = ?
                  AND year IN ({placeholders_years})
                  AND segment IN ({placeholders_segments})
                ORDER BY year, month, segment, customer_name
            """
            params = [account] + years + segments

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            if not rows:
                return False

            # UTF-8 with BOM で出力
            with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)

                # ヘッダー
                writer.writerow([
                    "年度", "月", "セグメント", "事業部", "部門名",
                    "取引先名", "業種", "科目", "金額"
                ])

                # データ
                for row in rows:
                    writer.writerow(row)

            return True

        except Exception as e:
            print(f"CSVエクスポートエラー: {e}")
            return False

    @staticmethod
    def get_default_filename(prefix: str = "会計データ") -> str:
        """デフォルトのファイル名を生成"""
        today = datetime.now().strftime("%Y%m%d")
        return f"{prefix}_{today}.csv"

    def close(self):
        """リソースを解放"""
        if self._owns_db and self.db:
            self.db.close()
