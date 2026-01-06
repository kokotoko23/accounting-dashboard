"""
データアクセス層 - SQLiteデータベースへのアクセスを提供
"""

import sqlite3
from pathlib import Path
from typing import List, Optional

import pandas as pd


class AccountingDatabase:
    """会計データベースアクセスクラス"""

    def __init__(self, db_path: Optional[str] = None):
        """
        データベース接続を初期化

        Args:
            db_path: データベースファイルのパス。指定しない場合はデフォルトパスを使用
        """
        if db_path is None:
            # デフォルトパス: プロジェクトルート/data/accounting.db
            project_root = Path(__file__).parent.parent.parent
            db_path = str(project_root / "data" / "accounting.db")

        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def connection(self) -> sqlite3.Connection:
        """データベース接続を取得（遅延接続）"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn

    def get_years(self) -> List[int]:
        """
        年度リストを取得

        Returns:
            年度のリスト（昇順）
        """
        query = """
            SELECT DISTINCT year
            FROM transactions_denormalized
            ORDER BY year
        """
        df = pd.read_sql_query(query, self.connection)
        return df["year"].tolist()

    def get_segments(self) -> List[str]:
        """
        セグメントリストを取得

        Returns:
            セグメント名のリスト
        """
        query = """
            SELECT DISTINCT segment
            FROM transactions_denormalized
            ORDER BY segment
        """
        df = pd.read_sql_query(query, self.connection)
        return df["segment"].tolist()

    def get_accounts(self) -> List[str]:
        """
        科目リストを取得

        Returns:
            科目名のリスト
        """
        query = """
            SELECT DISTINCT account
            FROM transactions_denormalized
            ORDER BY account
        """
        df = pd.read_sql_query(query, self.connection)
        return df["account"].tolist()

    def get_monthly_data(
        self,
        years: List[int],
        segments: List[str],
        account: str
    ) -> pd.DataFrame:
        """
        月次データを取得

        Args:
            years: 年度リスト
            segments: セグメントリスト
            account: 科目名

        Returns:
            月次集計データ（year, month, total）
        """
        if not years or not segments:
            return pd.DataFrame(columns=["year", "month", "total"])

        placeholders_years = ",".join("?" * len(years))
        placeholders_segments = ",".join("?" * len(segments))

        query = f"""
            SELECT year, month, SUM(amount) as total
            FROM transactions_denormalized
            WHERE account = ?
              AND year IN ({placeholders_years})
              AND segment IN ({placeholders_segments})
            GROUP BY year, month
            ORDER BY year, month
        """
        params = [account] + years + segments
        return pd.read_sql_query(query, self.connection, params=params)

    def get_segment_summary(
        self,
        years: List[int],
        account: str
    ) -> pd.DataFrame:
        """
        セグメント別集計を取得

        Args:
            years: 年度リスト
            account: 科目名

        Returns:
            セグメント別集計データ（segment, total）
        """
        if not years:
            return pd.DataFrame(columns=["segment", "total"])

        placeholders = ",".join("?" * len(years))

        query = f"""
            SELECT segment, SUM(amount) as total
            FROM transactions_denormalized
            WHERE account = ?
              AND year IN ({placeholders})
            GROUP BY segment
            ORDER BY total DESC
        """
        params = [account] + years
        return pd.read_sql_query(query, self.connection, params=params)

    def get_customer_ranking(
        self,
        year: int,
        account: str,
        limit: int = 20
    ) -> pd.DataFrame:
        """
        取引先ランキングを取得

        Args:
            year: 年度
            account: 科目名
            limit: 取得件数

        Returns:
            取引先ランキングデータ（customer_name, industry, total）
        """
        query = """
            SELECT customer_name, industry, SUM(amount) as total
            FROM transactions_denormalized
            WHERE account = ?
              AND year = ?
            GROUP BY customer_code, customer_name, industry
            ORDER BY total DESC
            LIMIT ?
        """
        return pd.read_sql_query(
            query, self.connection, params=[account, year, limit]
        )

    def get_industry_summary(
        self,
        year: int,
        account: str
    ) -> pd.DataFrame:
        """
        業種別集計を取得

        Args:
            year: 年度
            account: 科目名

        Returns:
            業種別集計データ（industry, total）
        """
        query = """
            SELECT industry, SUM(amount) as total
            FROM transactions_denormalized
            WHERE account = ?
              AND year = ?
            GROUP BY industry
            ORDER BY total DESC
        """
        return pd.read_sql_query(
            query, self.connection, params=[account, year]
        )

    def close(self):
        """データベース接続を閉じる"""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
