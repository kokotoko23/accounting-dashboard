"""
CSVインポーター - CSVファイルからデータベースへのインポート機能
ワイド形式（月別列）とロング形式の両方に対応
"""

import csv
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from app.models.database import AccountingDatabase


class CSVImporter:
    """CSVファイルをデータベースにインポートするクラス"""

    # ロング形式の必須カラム
    REQUIRED_COLUMNS_LONG = [
        "year", "month", "segment", "division", "dept_code", "dept_name",
        "customer_code", "customer_name", "industry", "account", "amount"
    ]

    # ワイド形式の必須カラム（月別列を除く）
    REQUIRED_COLUMNS_WIDE = [
        "year", "segment", "division", "dept_code", "dept_name",
        "customer_code", "customer_name", "industry", "account"
    ]

    # 月別カラム名
    MONTH_COLUMNS = ["1月", "2月", "3月", "4月", "5月", "6月",
                     "7月", "8月", "9月", "10月", "11月", "12月"]

    # カラム名の日本語マッピング
    COLUMN_MAPPING = {
        # 年度
        "年度": "year",
        "年": "year",
        # セグメント
        "セグメント": "segment",
        "開示セグメント名称": "segment",
        "開示セグメント": "segment",
        # 事業部
        "事業部": "division",
        "事業部名称": "division",
        "事業部名": "division",
        # 部門コード
        "部門コード": "dept_code",
        # 部門名
        "部門名": "dept_name",
        "部門名称": "dept_name",
        # 取引先コード
        "取引先コード": "customer_code",
        # 取引先名
        "取引先名": "customer_name",
        "取引先名称": "customer_name",
        # 業種
        "業種": "industry",
        "WITC業種名①": "industry",
        "WITC業種名": "industry",
        "業種名": "industry",
        # 科目
        "科目": "account",
        "科目名": "account",
        "科目名称": "account",
        # 金額（ロング形式用）
        "金額": "amount",
        # 月（ロング形式用）
        "月": "month",
    }

    # 無視するカラム
    IGNORE_COLUMNS = ["昇順", "合計", "順序"]

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

    def detect_format(self, df: pd.DataFrame) -> str:
        """
        CSVフォーマットを検出（ワイド形式 or ロング形式）

        Args:
            df: DataFrame

        Returns:
            "wide" または "long"
        """
        columns = df.columns.tolist()

        # 月別カラムがあればワイド形式
        month_cols_found = [col for col in columns if col in self.MONTH_COLUMNS]
        if len(month_cols_found) >= 6:  # 少なくとも6ヶ月分あれば
            return "wide"

        # month と amount カラムがあればロング形式
        if "month" in columns or "月" in columns:
            return "long"

        # カラム名をマッピング後に再チェック
        mapped_cols = []
        for col in columns:
            col_stripped = col.strip()
            if col_stripped in self.COLUMN_MAPPING:
                mapped_cols.append(self.COLUMN_MAPPING[col_stripped])
            else:
                mapped_cols.append(col_stripped)

        if "month" in mapped_cols:
            return "long"

        return "wide"  # デフォルトはワイド形式と仮定

    def transform_wide_to_long(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        ワイド形式をロング形式に変換

        Args:
            df: ワイド形式のDataFrame

        Returns:
            ロング形式のDataFrame
        """
        # カラム名を正規化
        df = self._normalize_columns(df)

        # 無視するカラムを削除
        for col in self.IGNORE_COLUMNS:
            if col in df.columns:
                df = df.drop(columns=[col])

        # 月別カラムを特定
        month_cols = [col for col in df.columns if col in self.MONTH_COLUMNS]

        if not month_cols:
            raise ValueError("月別カラム（1月〜12月）が見つかりません")

        # ID変数（月別以外のカラム）
        id_vars = [col for col in df.columns if col not in month_cols]

        # melt（ワイド→ロング変換）
        df_long = df.melt(
            id_vars=id_vars,
            value_vars=month_cols,
            var_name="month_name",
            value_name="amount"
        )

        # 月名を数値に変換
        month_map = {f"{i}月": i for i in range(1, 13)}
        df_long["month"] = df_long["month_name"].map(month_map)

        # month_name 列を削除
        df_long = df_long.drop(columns=["month_name"])

        # 金額が0または欠損の行を除外（オプション）
        df_long = df_long[df_long["amount"].notna() & (df_long["amount"] != 0)]

        return df_long

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

        # フォーマット検出
        csv_format = self.detect_format(df)
        print(f"検出されたCSVフォーマット: {csv_format}")

        # ワイド形式の場合はロング形式に変換
        if csv_format == "wide":
            try:
                df = self.transform_wide_to_long(df)
            except Exception as e:
                errors.append(f"ワイド→ロング変換エラー: {str(e)}")
                return False, pd.DataFrame(), errors
        else:
            # ロング形式の場合はカラム名を正規化
            df = self._normalize_columns(df)

        # 必須カラムチェック
        missing_columns = []
        for col in self.REQUIRED_COLUMNS_LONG:
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
        valid_months = df["month"].dropna()
        if len(valid_months) > 0:
            if (valid_months < 1).any() or (valid_months > 12).any():
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

            # マッピングに存在すれば変換
            if col_stripped in self.COLUMN_MAPPING:
                new_columns[col] = self.COLUMN_MAPPING[col_stripped]
            # 月別カラムはそのまま
            elif col_stripped in self.MONTH_COLUMNS:
                new_columns[col] = col_stripped
            # 無視するカラムはそのまま
            elif col_stripped in self.IGNORE_COLUMNS:
                new_columns[col] = col_stripped
            else:
                # 小文字に変換して比較
                col_lower = col_stripped.lower()
                matched = False
                for req_col in self.REQUIRED_COLUMNS_LONG:
                    if req_col.lower() == col_lower:
                        new_columns[col] = req_col
                        matched = True
                        break
                if not matched:
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

        # バリデーション（ワイド→ロング変換含む）
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
            for idx, row in df_clean.iterrows():
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
                    self.warnings.append(f"行 {idx + 2}: {str(e)}")

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
        サンプルCSVの内容を生成（ワイド形式）

        Returns:
            サンプルCSV文字列
        """
        header = "年度,開示セグメント名称,事業部名称,部門コード,部門名称,取引先コード,取引先名称,WITC業種名①,昇順,科目名称,1月,2月,3月,4月,5月,6月,7月,8月,9月,10月,11月,12月,合計"
        sample_rows = [
            "2024,製造事業,製造第一事業部,101,製造1課,130102,シータケミカル株式会社,化学,100,売上高,511926,598723,831515,593199,519499,546835,495901,617918,725707,721205,563740,866264,7592432",
        ]
        return header + "\n" + "\n".join(sample_rows)

    def close(self):
        """リソースを解放"""
        if self._owns_db and self.db:
            self.db.close()
