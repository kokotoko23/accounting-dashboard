# CLAUDE.md - Claude Code Project Configuration

## プロジェクト概要

会計データ可視化ダッシュボードアプリ（Windows exe配布用）

### 背景
- 月別の会計実績データ（数年分）を事業戦略に活用したい
- 将来的にkintone化を検討、まずPythonで活用イメージを固める
- 上司や関係者に配布するため、exe化したデスクトップアプリとして提供

## 技術スタック

- **Python**: 3.10+
- **GUI**: CustomTkinter（モダンなTkinter拡張）
- **グラフ**: matplotlib（Tkinter埋め込み）
- **データ**: SQLite + pandas
- **exe化**: PyInstaller

## ディレクトリ構造

```
accounting-dashboard/
├── app/                    # アプリ本体（これから開発）
│   ├── main.py            # エントリーポイント
│   ├── views/             # 画面コンポーネント
│   ├── models/            # データアクセス層
│   └── utils/             # ユーティリティ
├── data/                   # データファイル（.gitignoreで除外）
│   └── accounting.db      # SQLiteデータベース
├── docs/                   # ドキュメント
│   ├── REQUIREMENTS.md    # 詳細要件定義
│   └── CLAUDE_CODE_PROMPTS.md  # 開発用プロンプト集
├── scripts/                # データ処理スクリプト
│   ├── 01_generate_sample_data.py
│   ├── 02_transform_to_long.py
│   └── 03_validate_and_summarize.py
└── dist/                   # exe出力先
```

## データベース構造

### メインテーブル: transactions_denormalized

| カラム | 型 | 説明 |
|--------|-----|------|
| year | INTEGER | 年度（2022, 2023, 2024） |
| month | INTEGER | 月（1-12） |
| segment | TEXT | 開示セグメント名称 |
| division | TEXT | 事業部名称 |
| dept_code | TEXT | 部門コード |
| dept_name | TEXT | 部門名称 |
| customer_code | TEXT | 取引先コード |
| customer_name | TEXT | 取引先名称 |
| industry | TEXT | 業種 |
| account | TEXT | 科目名称 |
| amount | INTEGER | 金額 |

### 科目一覧
売上高, 売上原価, 販売費, 一般管理費, 営業外収益, 営業外費用

## 開発ルール

1. **日本語対応**: UI、コメントは日本語可
2. **データベースパス**: `data/accounting.db`
3. **グラフの日本語**: matplotlib で MS Gothic または Meiryo を使用
4. **exe化考慮**: 外部依存を最小限に

## 開発の進め方

`docs/CLAUDE_CODE_PROMPTS.md` に段階的なプロンプトがあります。
Phase 2-1-A から順に実行してください。

### クイックスタート

```bash
# 1. 依存パッケージ
pip install -r requirements.txt

# 2. サンプルデータ生成（初回のみ）
python scripts/01_generate_sample_data.py
python scripts/02_transform_to_long.py

# 3. アプリ開発開始
# docs/CLAUDE_CODE_PROMPTS.md の Phase 2-1-A を実行
```

## 参考SQLクエリ

### 月次売上推移
```sql
SELECT year, month, SUM(amount) as total
FROM transactions_denormalized
WHERE account = '売上高'
GROUP BY year, month
ORDER BY year, month
```

### セグメント別売上
```sql
SELECT segment, SUM(amount) as total
FROM transactions_denormalized
WHERE account = '売上高' AND year = 2024
GROUP BY segment
```

### 取引先ランキング
```sql
SELECT customer_name, industry, SUM(amount) as total
FROM transactions_denormalized
WHERE account = '売上高' AND year = 2024
GROUP BY customer_code, customer_name, industry
ORDER BY total DESC
LIMIT 20
```

## 詳細ドキュメント

- 要件定義: `docs/REQUIREMENTS.md`
- プロンプト集: `docs/CLAUDE_CODE_PROMPTS.md`
