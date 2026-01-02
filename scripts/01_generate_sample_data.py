"""
サンプル会計データ生成スクリプト
- 3年分（2022, 2023, 2024年度）
- ワイド形式（元のExcel形式を模倣）
"""

import pandas as pd
import numpy as np
from pathlib import Path
import random

# 乱数シード固定（再現性のため）
np.random.seed(42)
random.seed(42)

# =============================================================================
# マスタデータ定義
# =============================================================================

# セグメント → 事業部 の階層構造
SEGMENT_DIVISION = {
    "製造事業": ["製造第一事業部", "製造第二事業部"],
    "流通事業": ["流通営業部", "流通企画部"],
    "サービス事業": ["サービス開発部", "サービス運用部"],
}

# 事業部 → 部門 の階層構造
DIVISION_DEPT = {
    "製造第一事業部": [("101", "製造1課"), ("102", "製造2課")],
    "製造第二事業部": [("201", "製造3課"), ("202", "製造4課")],
    "流通営業部": [("301", "営業1課"), ("302", "営業2課")],
    "流通企画部": [("401", "企画課")],
    "サービス開発部": [("501", "開発1課"), ("502", "開発2課")],
    "サービス運用部": [("601", "運用課")],
}

# 取引先マスタ（コード、名称、業種）
CUSTOMERS = [
    ("110101", "アルファ電機株式会社", "電気電子"),
    ("110102", "ベータ工業株式会社", "電気電子"),
    ("110103", "ガンマテック株式会社", "電気電子"),
    ("120101", "デルタ機械株式会社", "機械"),
    ("120102", "イプシロン重工株式会社", "機械"),
    ("120103", "ゼータエンジニアリング株式会社", "機械"),
    ("130101", "イータ化学工業株式会社", "化学"),
    ("130102", "シータケミカル株式会社", "化学"),
    ("140101", "カッパ自動車株式会社", "自動車"),
    ("140102", "ラムダモーター株式会社", "自動車"),
    ("140103", "ミューオート株式会社", "自動車"),
    ("150101", "ニューフーズ株式会社", "食品"),
    ("150102", "クサイ食品株式会社", "食品"),
    ("160101", "オミクロン商事株式会社", "商社"),
    ("160102", "パイトレーディング株式会社", "商社"),
    ("160103", "ロー物産株式会社", "商社"),
    ("170101", "シグマIT株式会社", "情報通信"),
    ("170102", "タウシステムズ株式会社", "情報通信"),
    ("170103", "ウプシロンソフト株式会社", "情報通信"),
    ("170104", "ファイテクノロジー株式会社", "情報通信"),
    ("180101", "カイ建設株式会社", "建設"),
    ("180102", "プサイ工務店株式会社", "建設"),
    ("190101", "オメガ運輸株式会社", "物流"),
    ("190102", "アルファロジスティクス株式会社", "物流"),
    ("200101", "ベータ医薬株式会社", "医薬品"),
    ("200102", "ガンマファーマ株式会社", "医薬品"),
    ("210101", "デルタ金属株式会社", "金属"),
    ("210102", "イプシロン鋼業株式会社", "金属"),
    ("220101", "ゼータ繊維株式会社", "繊維"),
    ("220102", "イータテキスタイル株式会社", "繊維"),
    ("230101", "シータ精密株式会社", "精密機器"),
    ("230102", "カッパ計器株式会社", "精密機器"),
    ("240101", "ラムダ不動産株式会社", "不動産"),
    ("240102", "ミュープロパティ株式会社", "不動産"),
    ("250101", "ニューエナジー株式会社", "エネルギー"),
    ("250102", "クサイパワー株式会社", "エネルギー"),
    ("260101", "オミクロンサービス株式会社", "サービス"),
    ("260102", "パイコンサルティング株式会社", "サービス"),
    ("260103", "ロービジネス株式会社", "サービス"),
    ("270101", "シグマ小売株式会社", "小売"),
]

# 科目マスタ（科目名、ソート順、基準金額レンジ）
ACCOUNTS = [
    ("売上高", 100, (500000, 5000000)),
    ("売上原価", 200, (300000, 3000000)),
    ("販売費", 300, (50000, 500000)),
    ("一般管理費", 400, (30000, 300000)),
    ("営業外収益", 500, (10000, 100000)),
    ("営業外費用", 600, (5000, 50000)),
]

# 年度リスト
YEARS = [2022, 2023, 2024]

# 季節性係数（月ごとの売上変動）
SEASONALITY = {
    1: 0.85, 2: 0.80, 3: 1.20,  # Q4末（3月決算を想定）
    4: 0.90, 5: 0.95, 6: 1.00,
    7: 0.95, 8: 0.85, 9: 1.10,
    10: 1.05, 11: 1.10, 12: 1.15,
}


def generate_monthly_data(base_amount: float, year: int) -> dict:
    """月別データを生成（季節性＋ランダム変動）"""
    # 年度ごとの成長率
    growth_rate = {2022: 1.0, 2023: 1.05, 2024: 1.08}
    
    monthly = {}
    for month in range(1, 13):
        # 基準額 × 成長率 × 季節性 × ランダム変動
        value = (
            base_amount
            * growth_rate[year]
            * SEASONALITY[month]
            * np.random.uniform(0.8, 1.2)
        )
        monthly[f"{month}月"] = int(value)
    
    return monthly


def generate_sample_data() -> pd.DataFrame:
    """サンプルデータ生成"""
    records = []
    
    for year in YEARS:
        for segment, divisions in SEGMENT_DIVISION.items():
            for division in divisions:
                for dept_code, dept_name in DIVISION_DEPT[division]:
                    # 各部門に割り当てる取引先をランダムに選択（5〜10社）
                    num_customers = random.randint(5, 10)
                    selected_customers = random.sample(CUSTOMERS, num_customers)
                    
                    for cust_code, cust_name, industry in selected_customers:
                        for account_name, sort_order, (min_val, max_val) in ACCOUNTS:
                            # 基準金額をランダムに決定
                            base_amount = random.uniform(min_val, max_val)
                            
                            # 売上高以外は売上高に対する比率で調整
                            if account_name == "売上原価":
                                base_amount *= 0.6  # 原価率60%程度
                            elif account_name == "販売費":
                                base_amount *= 0.1
                            elif account_name == "一般管理費":
                                base_amount *= 0.05
                            elif account_name in ("営業外収益", "営業外費用"):
                                base_amount *= 0.02
                            
                            # 月別データ生成
                            monthly = generate_monthly_data(base_amount, year)
                            
                            # レコード作成
                            record = {
                                "年度": year,
                                "開示セグメント名称": segment,
                                "事業部名称": division,
                                "部門コード": dept_code,
                                "部門名称": dept_name,
                                "取引先コード": cust_code,
                                "取引先名称": cust_name,
                                "WITC業種名①": industry,
                                "昇順": sort_order,
                                "科目名称": account_name,
                                **monthly,
                            }
                            record["合計"] = sum(monthly.values())
                            records.append(record)
    
    df = pd.DataFrame(records)
    
    # カラム順序を整理
    cols = [
        "年度", "開示セグメント名称", "事業部名称", "部門コード", "部門名称",
        "取引先コード", "取引先名称", "WITC業種名①", "昇順", "科目名称",
        "1月", "2月", "3月", "4月", "5月", "6月",
        "7月", "8月", "9月", "10月", "11月", "12月", "合計"
    ]
    df = df[cols]
    
    return df


def main():
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("サンプルデータを生成中...")
    df = generate_sample_data()
    
    # 年度別にファイル出力（実際の運用を模倣）
    for year in YEARS:
        year_df = df[df["年度"] == year].drop(columns=["年度"])
        output_path = output_dir / f"会計実績_{year}年度.csv"
        year_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"  {output_path.name}: {len(year_df):,}件")
    
    # 全年度統合版も出力
    all_path = output_dir / "会計実績_全年度.csv"
    df.to_csv(all_path, index=False, encoding="utf-8-sig")
    print(f"  {all_path.name}: {len(df):,}件")
    
    # 統計情報
    print("\n=== データ統計 ===")
    print(f"総レコード数: {len(df):,}")
    print(f"取引先数: {df['取引先コード'].nunique()}")
    print(f"部門数: {df['部門コード'].nunique()}")
    print(f"セグメント: {df['開示セグメント名称'].unique().tolist()}")
    print(f"科目: {df['科目名称'].unique().tolist()}")


if __name__ == "__main__":
    main()
