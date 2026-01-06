"""
CSVインポーター - CSVファイルからデータベースへのインポート機能
"""

import csv
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from app.models.database import AccountingDatabase


class CSVImporter:
    """CSVファイルをデータベースにインポートするクラス"""

    # 必須カラム
    REQUIRED_COLUMNS = [
        "year", "month", "segment", "division", "dept_code", "dept_name",
        "customer_code", "customer_name", "industry", "account", "amount"
    ]

    # カラム名の日本語マッピング
    COLUMN_MAPPING = {
        "年度": "year",
        "年": "year",
        "月": "month",
        "セグメント": "segment",
        "事業部": "division",
        "部門コード": "dept_code",
        "部門名": "dept_name",
        "部門名称": "dept_name",
        "取引先コード": "customer_code",
        "取引先名": "customer_name",
        "取引先名称": "customer_name",
        "業種": "industry",
        "科目": "account",
        "科目名": "account",
        "科目名称": "account",
        "金額": "amount",
    }

    def __init__(self, db: Optional[AccountingDatabase] = None):
        """
        インポーターを初期化

        Args:
            db: データベース接続（Noneの場合は新規作成）
        """
        self.db = db if db else AccountingDatabase()
        self._owns_db = db is None
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def detect_encoding(self, filepath: str) -> str:
        """
        ファイルのエンコーディングを検出

        Args:
            filepath: CSVファイルパス

        Returns:
            検出されたエンコーディング
        """
        encodings = ["utf-8-sig", "utf-8", "shift_jis", "cp932", "euc-jp"]

        for encoding in encodings:
            try:
                with open(filepath, "r", encoding=encoding) as f:
                    f.read(1024)
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue

        return "utf-8"

    def validate_csv(self, filepath: str) -> Tuple[bool, pd.DataFrame, List[str]]:
        """
        CSVファイルを検証

        Args:
            filepath: CSVファイルパス

        Returns:
            (成功フラグ, DataFrame, エラーリスト)
        """
        errors = []

        # ファイル存在チェック
        if not Path(filepath).exists():
            errors.append(f"ファイルが見つかりません: {filepath}")
            return False, pd.DataFrame(), errors

        # エンコーディング検出
        encoding = self.detect_encoding(filepath)

        try:
            # CSVを読み込み
            df = pd.read_csv(filepath, encoding=encoding)
        except Exception as e:
            errors.append(f"CSV読み込みエラー: {str(e)}")
            return False, pd.DataFrame(), errors

        # カラム名を正規化（日本語→英語）
        df = self._normalize_columns(df)

        # 必須カラムチェック
        missing_columns = []
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                missing_columns.append(col)

        if missing_columns:
            errors.append(f"必須カラムがありません: {', '.join(missing_columns)}")
            return False, df, errors

        # データ型チェック・変換
        try:
            df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
            df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce").astype("Int64")
        except Exception as e:
            errors.append(f"データ型変換エラー: {str(e)}")
            return False, df, errors

        # 無効な行をチェック
        invalid_rows = df[
            df["year"].isna() | df["month"].isna() | df["amount"].isna()
        ]
        if len(invalid_rows) > 0:
            errors.append(f"{len(invalid_rows)}行のデータに数値変換エラーがあります")

        # 年度・月の範囲チェック
        if (df["month"] < 1).any() or (df["month"] > 12).any():
            errors.append("月は1-12の範囲で指定してください")

        if len(errors) > 0:
            return False, df, errors

        return True, df, []

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        カラム名を正規化（日本語→英語）

        Args:
            df: 元のDataFrame

        Returns:
            カラム名を正規化したDataFrame
        """
        new_columns = {}
        for col in df.columns:
            # 先頭・末尾の空白を除去
            col_stripped = col.strip()
            if col_stripped in self.COLUMN_MAPPING:
                new_columns[col] = self.COLUMN_MAPPING[col_stripped]
            else:
                # 小文字に変換して比較
                col_lower = col_stripped.lower()
                if col_lower in [c.lower() for c in self.REQUIRED_COLUMNS]:
                    # 英語カラム名をそのまま使用
                    for req_col in self.REQUIRED_COLUMNS:
                        if req_col.lower() == col_lower:
                            new_columns[col] = req_col
                            break
                else:
                    new_columns[col] = col_stripped

        return df.rename(columns=new_columns)

    def import_csv(
        self,
        filepath: str,
        mode: str = "append"
    ) -> Tuple[bool, int, List[str]]:
        """
        CSVファイルをデータベースにインポート

        Args:
            filepath: CSVファイルパス
            mode: "append"（追加）または "replace"（置換）

        Returns:
            (成功フラグ, インポート件数, エラーリスト)
        """
        self.errors = []
        self.warnings = []

        # バリデーション
        is_valid, df, validation_errors = self.validate_csv(filepath)
        if not is_valid:
            return False, 0, validation_errors

        # 無効な行を除外
        df_clean = df.dropna(subset=["year", "month", "amount"])

        if len(df_clean) == 0:
            return False, 0, ["インポート可能なデータがありません"]

        try:
            conn = self.db.connection

            # 置換モードの場合は既存データを削除
            if mode == "replace":
                conn.execute("DELETE FROM transactions_denormalized")
                conn.commit()

            # データを挿入
            inserted_count = 0
            for _, row in df_clean.iterrows():
                try:
                    conn.execute(
                        """
                        INSERT INTO transactions_denormalized
                        (year, month, segment, division, dept_code, dept_name,
                         customer_code, customer_name, industry, account, amount)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            int(row["year"]),
                            int(row["month"]),
                            str(row["segment"]),
                            str(row["division"]),
                            str(row["dept_code"]),
                            str(row["dept_name"]),
                            str(row["customer_code"]),
                            str(row["customer_name"]),
                            str(row["industry"]),
                            str(row["account"]),
                            int(row["amount"])
                        )
                    )
                    inserted_count += 1
                except Exception as e:
                    self.warnings.append(f"行 {_ + 2}: {str(e)}")

            conn.commit()

            if self.warnings:
                self.errors.extend(self.warnings[:5])  # 最初の5件のみ
                if len(self.warnings) > 5:
                    self.errors.append(f"...他 {len(self.warnings) - 5} 件の警告")

            return True, inserted_count, self.errors

        except Exception as e:
            return False, 0, [f"データベースエラー: {str(e)}"]

    def get_sample_csv_content(self) -> str:
        """
        サンプルCSVの内容を生成

        Returns:
            サンプルCSV文字列
        """
        header = ",".join(self.REQUIRED_COLUMNS)
        sample_rows = [
            "2024,1,セグメントA,事業部1,D001,営業1課,C001,株式会社サンプル,製造業,売上高,1000000",
            "2024,1,セグメントA,事業部1,D001,営業1課,C001,株式会社サンプル,製造業,売上原価,600000",
            "2024,2,セグメントA,事業部1,D001,営業1課,C002,サンプル商事,卸売業,売上高,500000",
        ]
        return header + "\n" + "\n".join(sample_rows)

    def close(self):
        """リソースを解放"""
        if self._owns_db and self.db:
            self.db.close()
