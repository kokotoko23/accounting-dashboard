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

    def get_divisions(self) -> List[str]:
        """
        事業部リストを取得

        Returns:
            事業部名のリスト
        """
        query = """
            SELECT DISTINCT division
            FROM transactions_denormalized
            ORDER BY division
        """
        df = pd.read_sql_query(query, self.connection)
        return df["division"].tolist()

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
        divisions: List[str],
        account: str
    ) -> pd.DataFrame:
        """
        月次データを取得（事業部フィルタ）

        Args:
            years: 年度リスト
            divisions: 事業部リスト
            account: 科目名

        Returns:
            月次集計データ（year, month, total）
        """
        if not years or not divisions:
            return pd.DataFrame(columns=["year", "month", "total"])

        placeholders_years = ",".join("?" * len(years))
        placeholders_divisions = ",".join("?" * len(divisions))

        query = f"""
            SELECT year, month, SUM(amount) as total
            FROM transactions_denormalized
            WHERE account = ?
              AND year IN ({placeholders_years})
              AND division IN ({placeholders_divisions})
            GROUP BY year, month
            ORDER BY year, month
        """
        params = [account] + years + divisions
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

    def get_division_summary(
        self,
        years: List[int],
        account: str
    ) -> pd.DataFrame:
        """
        事業部別集計を取得

        Args:
            years: 年度リスト
            account: 科目名

        Returns:
            事業部別集計データ（division, total）
        """
        if not years:
            return pd.DataFrame(columns=["division", "total"])

        placeholders = ",".join("?" * len(years))

        query = f"""
            SELECT division, SUM(amount) as total
            FROM transactions_denormalized
            WHERE account = ?
              AND year IN ({placeholders})
            GROUP BY division
            ORDER BY total DESC
        """
        params = [account] + years
        return pd.read_sql_query(query, self.connection, params=params)

    def get_division_profit_summary(
        self,
        years: List[int]
    ) -> pd.DataFrame:
        """
        事業部別の売上・利益集計を取得

        Args:
            years: 年度リスト

        Returns:
            事業部別集計データ（division, sales, cost, profit）
        """
        if not years:
            return pd.DataFrame(columns=["division", "sales", "cost", "profit"])

        placeholders = ",".join("?" * len(years))

        query = f"""
            SELECT
                division,
                SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) as sales,
                SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as cost,
                SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) -
                SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as profit
            FROM transactions_denormalized
            WHERE year IN ({placeholders})
            GROUP BY division
            ORDER BY sales DESC
        """
        params = years
        return pd.read_sql_query(query, self.connection, params=params)

    def get_division_monthly_profit(
        self,
        years: List[int],
        divisions: List[str]
    ) -> pd.DataFrame:
        """
        事業部別の月次売上・利益推移を取得

        Args:
            years: 年度リスト
            divisions: 事業部リスト

        Returns:
            月次集計データ（year, month, sales, cost, profit）
        """
        if not years or not divisions:
            return pd.DataFrame(columns=["year", "month", "sales", "cost", "profit"])

        placeholders_years = ",".join("?" * len(years))
        placeholders_divisions = ",".join("?" * len(divisions))

        query = f"""
            SELECT
                year, month,
                SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) as sales,
                SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as cost,
                SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) -
                SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as profit
            FROM transactions_denormalized
            WHERE year IN ({placeholders_years})
              AND division IN ({placeholders_divisions})
            GROUP BY year, month
            ORDER BY year, month
        """
        params = years + divisions
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

    def get_customer_ranking_by_division(
        self,
        year: int,
        division: str,
        limit: int = 20
    ) -> pd.DataFrame:
        """
        事業部別の取引先ランキングを取得（売上高ベース）

        Args:
            year: 年度
            division: 事業部名
            limit: 取得件数

        Returns:
            取引先ランキングデータ（customer_name, industry, total）
        """
        query = """
            SELECT customer_name, industry, SUM(amount) as total
            FROM transactions_denormalized
            WHERE account = '売上高'
              AND year = ?
              AND division = ?
            GROUP BY customer_code, customer_name, industry
            ORDER BY total DESC
            LIMIT ?
        """
        return pd.read_sql_query(
            query, self.connection, params=[year, division, limit]
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

    def get_industry_summary_by_division(
        self,
        year: int,
        division: str
    ) -> pd.DataFrame:
        """
        事業部別の業種別集計を取得（売上高ベース）

        Args:
            year: 年度
            division: 事業部名

        Returns:
            業種別集計データ（industry, total）
        """
        query = """
            SELECT industry, SUM(amount) as total
            FROM transactions_denormalized
            WHERE account = '売上高'
              AND year = ?
              AND division = ?
            GROUP BY industry
            ORDER BY total DESC
        """
        return pd.read_sql_query(
            query, self.connection, params=[year, division]
        )

    def get_customer_profit_trend(
        self,
        years: List[int],
        customer_code: str
    ) -> pd.DataFrame:
        """
        取引先別の月次売上・利益推移を取得

        Args:
            years: 年度リスト
            customer_code: 取引先コード

        Returns:
            月次集計データ（year, month, sales, cost, profit）
        """
        if not years:
            return pd.DataFrame(columns=["year", "month", "sales", "cost", "profit"])

        placeholders = ",".join("?" * len(years))

        query = f"""
            SELECT
                year, month,
                SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) as sales,
                SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as cost,
                SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) -
                SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as profit
            FROM transactions_denormalized
            WHERE year IN ({placeholders})
              AND customer_code = ?
            GROUP BY year, month
            ORDER BY year, month
        """
        params = years + [customer_code]
        return pd.read_sql_query(query, self.connection, params=params)

    def get_industry_profit_trend(
        self,
        years: List[int],
        industry: str
    ) -> pd.DataFrame:
        """
        業種別の月次売上・利益推移を取得

        Args:
            years: 年度リスト
            industry: 業種名

        Returns:
            月次集計データ（year, month, sales, cost, profit）
        """
        if not years:
            return pd.DataFrame(columns=["year", "month", "sales", "cost", "profit"])

        placeholders = ",".join("?" * len(years))

        query = f"""
            SELECT
                year, month,
                SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) as sales,
                SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as cost,
                SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) -
                SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as profit
            FROM transactions_denormalized
            WHERE year IN ({placeholders})
              AND industry = ?
            GROUP BY year, month
            ORDER BY year, month
        """
        params = years + [industry]
        return pd.read_sql_query(query, self.connection, params=params)

    def get_dept_codes(self) -> pd.DataFrame:
        """
        部門コードリストを取得

        Returns:
            部門コードと部門名のDataFrame（dept_code, dept_name）
        """
        query = """
            SELECT DISTINCT dept_code, dept_name
            FROM transactions_denormalized
            ORDER BY dept_code
        """
        return pd.read_sql_query(query, self.connection)

    def get_depts_by_division(self, division: str) -> pd.DataFrame:
        """
        指定事業部の部門リストを取得

        Args:
            division: 事業部名

        Returns:
            部門コードと部門名のDataFrame（dept_code, dept_name）
        """
        query = """
            SELECT DISTINCT dept_code, dept_name
            FROM transactions_denormalized
            WHERE division = ?
            ORDER BY dept_code
        """
        return pd.read_sql_query(query, self.connection, params=[division])

    def get_dept_summary(
        self,
        years: List[int],
        account: str
    ) -> pd.DataFrame:
        """
        部門別集計を取得

        Args:
            years: 年度リスト
            account: 科目名

        Returns:
            部門別集計データ（dept_code, dept_name, total）
        """
        if not years:
            return pd.DataFrame(columns=["dept_code", "dept_name", "total"])

        placeholders = ",".join("?" * len(years))

        query = f"""
            SELECT dept_code, MAX(dept_name) as dept_name, SUM(amount) as total
            FROM transactions_denormalized
            WHERE account = ?
              AND year IN ({placeholders})
            GROUP BY dept_code
            ORDER BY total DESC
        """
        params = [account] + years
        return pd.read_sql_query(query, self.connection, params=params)

    def get_dept_profit_summary(
        self,
        years: List[int]
    ) -> pd.DataFrame:
        """
        部門別の売上・利益集計を取得

        Args:
            years: 年度リスト

        Returns:
            部門別集計データ（dept_code, dept_name, sales, cost, profit）
        """
        if not years:
            return pd.DataFrame(columns=["dept_code", "dept_name", "sales", "cost", "profit"])

        placeholders = ",".join("?" * len(years))

        query = f"""
            SELECT
                dept_code,
                MAX(dept_name) as dept_name,
                SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) as sales,
                SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as cost,
                SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) -
                SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as profit
            FROM transactions_denormalized
            WHERE year IN ({placeholders})
            GROUP BY dept_code
            ORDER BY sales DESC
        """
        params = years
        return pd.read_sql_query(query, self.connection, params=params)

    def get_dept_summary_by_division(
        self,
        years: List[int],
        division: str,
        account: str
    ) -> pd.DataFrame:
        """
        指定事業部の部門別集計を取得

        Args:
            years: 年度リスト
            division: 事業部名
            account: 科目名

        Returns:
            部門別集計データ（dept_code, dept_name, total）
        """
        if not years:
            return pd.DataFrame(columns=["dept_code", "dept_name", "total"])

        placeholders = ",".join("?" * len(years))

        query = f"""
            SELECT dept_code, MAX(dept_name) as dept_name, SUM(amount) as total
            FROM transactions_denormalized
            WHERE account = ?
              AND division = ?
              AND year IN ({placeholders})
            GROUP BY dept_code
            ORDER BY total DESC
        """
        params = [account, division] + years
        return pd.read_sql_query(query, self.connection, params=params)

    def get_dept_profit_summary_by_division(
        self,
        years: List[int],
        division: str,
        dept_codes: List[str] = None
    ) -> pd.DataFrame:
        """
        指定事業部の部門別売上・利益集計を取得

        Args:
            years: 年度リスト
            division: 事業部名
            dept_codes: 部門コードリスト（指定しない場合は全部門）

        Returns:
            部門別集計データ（dept_code, dept_name, sales, cost, profit）
        """
        if not years:
            return pd.DataFrame(columns=["dept_code", "dept_name", "sales", "cost", "profit"])

        placeholders_years = ",".join("?" * len(years))

        if dept_codes:
            placeholders_depts = ",".join("?" * len(dept_codes))
            query = f"""
                SELECT
                    dept_code,
                    MAX(dept_name) as dept_name,
                    SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) as sales,
                    SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as cost,
                    SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) -
                    SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as profit
                FROM transactions_denormalized
                WHERE division = ?
                  AND year IN ({placeholders_years})
                  AND dept_code IN ({placeholders_depts})
                GROUP BY dept_code
                ORDER BY sales DESC
            """
            params = [division] + years + dept_codes
        else:
            query = f"""
                SELECT
                    dept_code,
                    MAX(dept_name) as dept_name,
                    SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) as sales,
                    SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as cost,
                    SUM(CASE WHEN account = '売上高' THEN amount ELSE 0 END) -
                    SUM(CASE WHEN account = '売上原価' THEN amount ELSE 0 END) as profit
                FROM transactions_denormalized
                WHERE division = ?
                  AND year IN ({placeholders_years})
                GROUP BY dept_code
                ORDER BY sales DESC
            """
            params = [division] + years

        return pd.read_sql_query(query, self.connection, params=params)

    def get_dept_monthly_data(
        self,
        years: List[int],
        division: str,
        dept_codes: List[str],
        account: str
    ) -> pd.DataFrame:
        """
        部門別月次データを取得

        Args:
            years: 年度リスト
            division: 事業部名
            dept_codes: 部門コードリスト
            account: 科目名

        Returns:
            月次集計データ（year, month, dept_code, dept_name, total）
        """
        if not years or not dept_codes:
            return pd.DataFrame(columns=["year", "month", "dept_code", "dept_name", "total"])

        placeholders_years = ",".join("?" * len(years))
        placeholders_depts = ",".join("?" * len(dept_codes))

        query = f"""
            SELECT year, month, dept_code, MAX(dept_name) as dept_name, SUM(amount) as total
            FROM transactions_denormalized
            WHERE account = ?
              AND division = ?
              AND year IN ({placeholders_years})
              AND dept_code IN ({placeholders_depts})
            GROUP BY year, month, dept_code
            ORDER BY year, month, dept_code
        """
        params = [account, division] + years + dept_codes
        return pd.read_sql_query(query, self.connection, params=params)

    def close(self):
        """データベース接続を閉じる"""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
