# 会計データ可視化プロジェクト 要件定義書

## プロジェクト概要

### 背景
- 月別の会計実績データ（数年分）を事業戦略に活用したい
- 現状はExcelファイルがフォルダに格納されている
- 将来的にはkintone化を検討しているが、まずPythonで活用イメージを固めたい
- 上司や関係者に配布するため、exe化したデスクトップアプリとして提供する

### 目的
Phase 2: データ可視化ダッシュボードアプリの開発（exe配布可能）

---

## 技術要件

### 使用技術
- **言語**: Python 3.10+
- **GUIフレームワーク**: CustomTkinter（モダンなUI、exe化容易）
- **グラフライブラリ**: matplotlib（Tkinter埋め込み対応）
- **データ処理**: pandas, sqlite3
- **exe化**: PyInstaller

### ディレクトリ構成
```
accounting_project/
├── data/
│   ├── accounting.db          # SQLiteデータベース（生成済み）
│   ├── 会計実績_YYYY年度.csv   # 元データ（ワイド形式）
│   └── transactions_long.csv  # ロング形式CSV
├── scripts/
│   ├── 01_generate_sample_data.py
│   ├── 02_transform_to_long.py
│   └── 03_validate_and_summarize.py
├── app/                       # ← 新規作成
│   ├── main.py               # エントリーポイント
│   ├── views/                # 画面コンポーネント
│   ├── models/               # データアクセス層
│   └── utils/                # ユーティリティ
├── docs/
│   └── REQUIREMENTS.md       # この文書
└── dist/                     # exe出力先
```

---

## データ構造

### データベース: accounting.db

#### transactions_denormalized（メインテーブル）
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
| industry | TEXT | 業種（WITC業種名①） |
| account | TEXT | 科目名称 |
| amount | INTEGER | 金額 |

#### カラム名対応（元データ → DB）
| 元カラム名 | DBカラム名 |
|-----------|-----------|
| 開示セグメント名称 | segment |
| 事業部名称 | division |
| 部門コード | dept_code |
| 部門名称 | dept_name |
| 取引先コード | customer_code |
| 取引先名称 | customer_name |
| WITC業種名① | industry |
| 科目名称 | account |
| 1月〜12月 | month + amount（ロング形式に展開） |

#### 科目一覧
- 売上高
- 売上原価
- 販売費
- 一般管理費
- 営業外収益
- 営業外費用

---

## 機能要件

### 画面構成

#### 1. メイン画面（ダッシュボード）
- **フィルタパネル**（左側または上部）
  - 年度選択（複数選択可、デフォルト: 全年度）
  - セグメント選択（複数選択可）
  - 科目選択（デフォルト: 売上高）
  
- **グラフエリア**（メイン）
  - 月次推移グラフ（折れ線）
  - セグメント別構成比（円グラフまたは棒グラフ）
  - 前年同月比較グラフ

- **サマリーパネル**
  - 選択期間の合計金額
  - 前年比（%）
  - 取引先数

#### 2. 取引先分析画面
- 取引先ランキング（売上高TOP20）
- 業種別構成比
- 取引先別推移（選択した取引先の月次推移）

#### 3. セグメント分析画面
- セグメント別年度推移
- 事業部別ドリルダウン
- 部門別詳細

### 操作要件
- フィルタ変更時にグラフが即時更新
- グラフはマウスホバーで数値表示（可能であれば）
- データのCSVエクスポート機能

---

## 非機能要件

### パフォーマンス
- 起動時間: 5秒以内
- フィルタ変更後の描画: 1秒以内

### 配布
- 単一exeファイルまたはフォルダ形式で配布
- データベースファイル（accounting.db）は同梱または外部参照
- Windows 10/11対応

### UI/UX
- ダークモード対応（CustomTkinterのテーマ機能）
- 日本語表示（文字化けなし）
- 画面サイズ: 1280x800以上推奨

---

## 開発フェーズ

### Phase 2-1: 基本UI構築
- [ ] CustomTkinterでメインウィンドウ作成
- [ ] フィルタパネル実装
- [ ] タブ切り替え実装

### Phase 2-2: グラフ実装
- [ ] matplotlib埋め込み
- [ ] 月次推移グラフ
- [ ] 構成比グラフ
- [ ] 前年比較グラフ

### Phase 2-3: データ連携
- [ ] SQLiteからのデータ読み込み
- [ ] フィルタ条件に応じたクエリ生成
- [ ] グラフ更新ロジック

### Phase 2-4: 追加機能
- [ ] CSVエクスポート
- [ ] 取引先分析画面
- [ ] セグメント分析画面

### Phase 2-5: exe化・配布準備
- [ ] PyInstallerでexe化
- [ ] 動作確認
- [ ] README作成

---

## 補足情報

### サンプルSQLクエリ

#### 月次売上推移
```sql
SELECT year, month, SUM(amount) as total
FROM transactions_denormalized
WHERE account = '売上高'
GROUP BY year, month
ORDER BY year, month
```

#### セグメント別売上
```sql
SELECT segment, SUM(amount) as total
FROM transactions_denormalized
WHERE account = '売上高' AND year = 2024
GROUP BY segment
```

#### 取引先ランキング
```sql
SELECT customer_name, industry, SUM(amount) as total
FROM transactions_denormalized
WHERE account = '売上高' AND year = 2024
GROUP BY customer_code, customer_name, industry
ORDER BY total DESC
LIMIT 20
```

### 参考リンク
- CustomTkinter: https://github.com/TomSchimansky/CustomTkinter
- matplotlib Tkinter embedding: https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_tk_sgskip.html
- PyInstaller: https://pyinstaller.org/
