"""
基本集計・データ検証スクリプト
SQLiteからデータを読み込み、各種集計を実行
"""

import pandas as pd
import sqlite3
from pathlib import Path


def connect_db(db_path: Path) -> sqlite3.Connection:
    """DB接続"""
    return sqlite3.connect(db_path)


def validate_data(conn: sqlite3.Connection):
    """データ検証"""
    print("=" * 60)
    print("データ検証")
    print("=" * 60)
    
    # 基本統計
    query = """
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT year) as years,
        COUNT(DISTINCT customer_code) as customers,
        COUNT(DISTINCT dept_code) as departments,
        COUNT(DISTINCT account) as accounts,
        SUM(amount) as total_amount
    FROM transactions_denormalized
    """
    stats = pd.read_sql(query, conn)
    print("\n【基本統計】")
    print(f"  総レコード数: {stats['total_records'].iloc[0]:,}")
    print(f"  年度数: {stats['years'].iloc[0]}")
    print(f"  取引先数: {stats['customers'].iloc[0]}")
    print(f"  部門数: {stats['departments'].iloc[0]}")
    print(f"  科目数: {stats['accounts'].iloc[0]}")
    print(f"  総金額: ¥{stats['total_amount'].iloc[0]:,.0f}")
    
    # NULL/欠損値チェック
    query = """
    SELECT 
        SUM(CASE WHEN year IS NULL THEN 1 ELSE 0 END) as null_year,
        SUM(CASE WHEN month IS NULL THEN 1 ELSE 0 END) as null_month,
        SUM(CASE WHEN customer_code IS NULL THEN 1 ELSE 0 END) as null_customer,
        SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END) as null_amount
    FROM transactions_denormalized
    """
    nulls = pd.read_sql(query, conn)
    print("\n【NULL値チェック】")
    print(f"  year: {nulls['null_year'].iloc[0]}")
    print(f"  month: {nulls['null_month'].iloc[0]}")
    print(f"  customer_code: {nulls['null_customer'].iloc[0]}")
    print(f"  amount: {nulls['null_amount'].iloc[0]}")


def yearly_summary(conn: sqlite3.Connection):
    """年度別サマリー"""
    print("\n" + "=" * 60)
    print("年度別サマリー")
    print("=" * 60)
    
    query = """
    SELECT 
        year as 年度,
        account as 科目,
        SUM(amount) as 金額
    FROM transactions_denormalized
    GROUP BY year, account
    ORDER BY year, 
        CASE account 
            WHEN '売上高' THEN 1
            WHEN '売上原価' THEN 2
            WHEN '販売費' THEN 3
            WHEN '一般管理費' THEN 4
            WHEN '営業外収益' THEN 5
            WHEN '営業外費用' THEN 6
        END
    """
    df = pd.read_sql(query, conn)
    
    # ピボット形式で表示
    pivot = df.pivot(index="科目", columns="年度", values="金額")
    pivot = pivot.reindex(["売上高", "売上原価", "販売費", "一般管理費", "営業外収益", "営業外費用"])
    
    print("\n【科目別年度推移】")
    print(pivot.map(lambda x: f"¥{x:,.0f}" if pd.notna(x) else "-").to_string())
    
    # 前年比計算
    print("\n【前年比】")
    for col in [2023, 2024]:
        if col in pivot.columns and col-1 in pivot.columns:
            yoy = (pivot[col] / pivot[col-1] - 1) * 100
            print(f"\n{col}年度 vs {col-1}年度:")
            for idx, val in yoy.items():
                print(f"  {idx}: {val:+.1f}%")


def segment_summary(conn: sqlite3.Connection):
    """セグメント別サマリー"""
    print("\n" + "=" * 60)
    print("セグメント別サマリー（売上高のみ）")
    print("=" * 60)
    
    query = """
    SELECT 
        year as 年度,
        segment as セグメント,
        SUM(amount) as 売上高
    FROM transactions_denormalized
    WHERE account = '売上高'
    GROUP BY year, segment
    ORDER BY year, segment
    """
    df = pd.read_sql(query, conn)
    pivot = df.pivot(index="セグメント", columns="年度", values="売上高")
    
    print("\n【セグメント別売上推移】")
    print(pivot.map(lambda x: f"¥{x:,.0f}" if pd.notna(x) else "-").to_string())
    
    # 構成比
    print("\n【セグメント構成比】")
    for col in pivot.columns:
        total = pivot[col].sum()
        print(f"\n{col}年度:")
        for idx, val in pivot[col].items():
            pct = val / total * 100
            print(f"  {idx}: {pct:.1f}%")


def monthly_trend(conn: sqlite3.Connection):
    """月次推移"""
    print("\n" + "=" * 60)
    print("月次推移（売上高）")
    print("=" * 60)
    
    query = """
    SELECT 
        year as 年度,
        month as 月,
        SUM(amount) as 売上高
    FROM transactions_denormalized
    WHERE account = '売上高'
    GROUP BY year, month
    ORDER BY year, month
    """
    df = pd.read_sql(query, conn)
    pivot = df.pivot(index="月", columns="年度", values="売上高")
    
    print("\n【月別売上推移】")
    print(pivot.map(lambda x: f"¥{x:,.0f}" if pd.notna(x) else "-").to_string())


def top_customers(conn: sqlite3.Connection, year: int = 2024, top_n: int = 10):
    """取引先ランキング"""
    print("\n" + "=" * 60)
    print(f"取引先ランキング TOP{top_n}（{year}年度 売上高）")
    print("=" * 60)
    
    query = f"""
    SELECT 
        customer_code as 取引先コード,
        customer_name as 取引先名,
        industry as 業種,
        SUM(amount) as 売上高
    FROM transactions_denormalized
    WHERE account = '売上高' AND year = {year}
    GROUP BY customer_code, customer_name, industry
    ORDER BY 売上高 DESC
    LIMIT {top_n}
    """
    df = pd.read_sql(query, conn)
    
    print()
    for i, row in df.iterrows():
        print(f"{i+1:2d}. {row['取引先名'][:20]:<22} ({row['業種']:<6}) ¥{row['売上高']:>15,.0f}")


def industry_analysis(conn: sqlite3.Connection):
    """業種別分析"""
    print("\n" + "=" * 60)
    print("業種別売上分析")
    print("=" * 60)
    
    query = """
    SELECT 
        year as 年度,
        industry as 業種,
        SUM(amount) as 売上高,
        COUNT(DISTINCT customer_code) as 取引先数
    FROM transactions_denormalized
    WHERE account = '売上高'
    GROUP BY year, industry
    ORDER BY year, 売上高 DESC
    """
    df = pd.read_sql(query, conn)
    
    # 最新年度の業種別
    latest_year = df["年度"].max()
    latest = df[df["年度"] == latest_year].copy()
    latest["構成比"] = latest["売上高"] / latest["売上高"].sum() * 100
    
    print(f"\n【{latest_year}年度 業種別売上】")
    for _, row in latest.iterrows():
        print(f"  {row['業種']:<8} ¥{row['売上高']:>15,.0f} ({row['構成比']:5.1f}%) 取引先{row['取引先数']:2d}社")


def main():
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / "data" / "accounting.db"
    
    if not db_path.exists():
        print(f"ERROR: データベースが見つかりません: {db_path}")
        print("先に 02_transform_to_long.py を実行してください。")
        return
    
    conn = connect_db(db_path)
    
    try:
        validate_data(conn)
        yearly_summary(conn)
        segment_summary(conn)
        monthly_trend(conn)
        top_customers(conn)
        industry_analysis(conn)
    finally:
        conn.close()
    
    print("\n" + "=" * 60)
    print("検証完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
