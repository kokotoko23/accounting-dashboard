"""
ワイド形式 → ロング形式変換 + SQLite格納スクリプト
"""

import pandas as pd
import sqlite3
from pathlib import Path

# =============================================================================
# カラム名対応辞書
# =============================================================================
COLUMN_MAPPING = {
    "年度": "year",
    "開示セグメント名称": "segment",
    "事業部名称": "division",
    "部門コード": "dept_code",
    "部門名称": "dept_name",
    "取引先コード": "customer_code",
    "取引先名称": "customer_name",
    "WITC業種名①": "industry",
    "昇順": "sort_order",  # 変換後は削除
    "科目名称": "account",
}

# 月カラム（ワイド形式でのカラム名）
MONTH_COLUMNS = [f"{i}月" for i in range(1, 13)]


def load_wide_data(data_dir: Path) -> pd.DataFrame:
    """年度別CSVを読み込み、統合"""
    dfs = []
    
    for csv_path in sorted(data_dir.glob("会計実績_*年度.csv")):
        # 全年度ファイルはスキップ
        if "全年度" in csv_path.name:
            continue
        # ファイル名から年度を抽出
        year = int(csv_path.stem.split("_")[1].replace("年度", ""))
        
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        df["年度"] = year
        dfs.append(df)
        print(f"  読込: {csv_path.name} ({len(df):,}件)")
    
    return pd.concat(dfs, ignore_index=True)


def wide_to_long(df: pd.DataFrame) -> pd.DataFrame:
    """ワイド形式 → ロング形式に変換"""
    # ID列（月以外の属性）
    id_vars = [col for col in df.columns if col not in MONTH_COLUMNS + ["合計"]]
    
    # meltでロング形式に変換
    df_long = df.melt(
        id_vars=id_vars,
        value_vars=MONTH_COLUMNS,
        var_name="月_jp",
        value_name="amount"
    )
    
    # 月を数値に変換（"1月" → 1）
    df_long["month"] = df_long["月_jp"].str.replace("月", "").astype(int)
    df_long = df_long.drop(columns=["月_jp"])
    
    # カラム名を英語に変換
    df_long = df_long.rename(columns=COLUMN_MAPPING)
    
    # sort_order（昇順）は削除
    if "sort_order" in df_long.columns:
        df_long = df_long.drop(columns=["sort_order"])
    
    # カラム順序を整理
    cols = [
        "year", "month", "segment", "division", "dept_code", "dept_name",
        "customer_code", "customer_name", "industry", "account", "amount"
    ]
    df_long = df_long[cols]
    
    return df_long


def create_master_tables(df_long: pd.DataFrame) -> tuple:
    """マスタテーブルを生成"""
    # 取引先マスタ
    customers = df_long[["customer_code", "customer_name", "industry"]].drop_duplicates()
    customers = customers.sort_values("customer_code").reset_index(drop=True)
    
    # 部門マスタ
    departments = df_long[["dept_code", "dept_name", "division", "segment"]].drop_duplicates()
    departments = departments.sort_values("dept_code").reset_index(drop=True)
    
    # 科目マスタ
    accounts = df_long[["account"]].drop_duplicates()
    accounts["account_code"] = range(1, len(accounts) + 1)
    accounts = accounts[["account_code", "account"]]
    
    return customers, departments, accounts


def normalize_transaction(df_long: pd.DataFrame) -> pd.DataFrame:
    """トランザクションテーブルを正規化（マスタ参照のみに）"""
    # 正規化版（マスタは別テーブル参照）
    transaction = df_long[[
        "year", "month", "dept_code", "customer_code", "account", "amount"
    ]].copy()
    
    return transaction


def save_to_sqlite(
    df_long: pd.DataFrame,
    customers: pd.DataFrame,
    departments: pd.DataFrame,
    accounts: pd.DataFrame,
    transaction: pd.DataFrame,
    db_path: Path
):
    """SQLiteに保存"""
    conn = sqlite3.connect(db_path)
    
    # テーブル作成・データ挿入
    df_long.to_sql("transactions_denormalized", conn, if_exists="replace", index=False)
    customers.to_sql("m_customers", conn, if_exists="replace", index=False)
    departments.to_sql("m_departments", conn, if_exists="replace", index=False)
    accounts.to_sql("m_accounts", conn, if_exists="replace", index=False)
    transaction.to_sql("transactions", conn, if_exists="replace", index=False)
    
    # インデックス作成
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_year_month ON transactions(year, month)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_customer ON transactions(customer_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_dept ON transactions(dept_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trans_account ON transactions(account)")
    
    conn.commit()
    conn.close()
    
    print(f"\nSQLite保存完了: {db_path}")


def main():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    db_path = data_dir / "accounting.db"
    
    print("=== ワイド形式データ読込 ===")
    df_wide = load_wide_data(data_dir)
    print(f"統合後: {len(df_wide):,}件")
    
    print("\n=== ロング形式に変換 ===")
    df_long = wide_to_long(df_wide)
    print(f"変換後: {len(df_long):,}件")
    print(f"カラム: {df_long.columns.tolist()}")
    
    print("\n=== マスタテーブル生成 ===")
    customers, departments, accounts = create_master_tables(df_long)
    print(f"取引先マスタ: {len(customers)}件")
    print(f"部門マスタ: {len(departments)}件")
    print(f"科目マスタ: {len(accounts)}件")
    
    print("\n=== トランザクション正規化 ===")
    transaction = normalize_transaction(df_long)
    print(f"正規化トランザクション: {len(transaction):,}件")
    
    print("\n=== SQLite保存 ===")
    save_to_sqlite(df_long, customers, departments, accounts, transaction, db_path)
    
    # ロング形式CSVも出力（確認用）
    csv_path = data_dir / "transactions_long.csv"
    df_long.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"CSV出力: {csv_path}")
    
    # サンプル表示
    print("\n=== 変換後サンプル（先頭5件）===")
    print(df_long.head().to_string())


if __name__ == "__main__":
    main()
