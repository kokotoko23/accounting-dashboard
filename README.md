# 会計データ可視化ダッシュボード

月別会計実績データを可視化・分析するデスクトップアプリケーション。

## 概要

- **目的**: 会計データの可視化により、事業戦略への活用を促進
- **将来計画**: kintone移行前の活用イメージ検証
- **配布形式**: Windows exe（PyInstaller）

## 機能

- 月次推移グラフ（年度比較）
- セグメント別構成比
- 取引先ランキング
- 業種別分析
- CSVエクスポート

## 技術スタック

| カテゴリ | 技術 |
|----------|------|
| 言語 | Python 3.10+ |
| GUI | CustomTkinter |
| グラフ | matplotlib |
| データ | SQLite, pandas |
| 配布 | PyInstaller |

## セットアップ

```bash
# 依存パッケージインストール
pip install -r requirements.txt

# サンプルデータ生成
python scripts/01_generate_sample_data.py
python scripts/02_transform_to_long.py

# データ検証
python scripts/03_validate_and_summarize.py

# アプリ起動（開発後）
python app/main.py
```

## ディレクトリ構成

```
accounting-dashboard/
├── app/                # アプリ本体
├── data/               # データベース・CSV（gitignore）
├── docs/               # ドキュメント
│   ├── REQUIREMENTS.md
│   └── CLAUDE_CODE_PROMPTS.md
├── scripts/            # データ処理スクリプト
├── CLAUDE.md           # Claude Code設定
└── requirements.txt
```

## 開発状況

- [x] Phase 1: データ設計・変換処理
- [ ] Phase 2: 可視化ダッシュボード
- [ ] Phase 3: 分析機能
- [ ] Phase 4: exe化・配布

## ドキュメント

- [要件定義書](docs/REQUIREMENTS.md)
- [Claude Codeプロンプト集](docs/CLAUDE_CODE_PROMPTS.md)
