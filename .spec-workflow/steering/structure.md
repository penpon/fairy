# Project Structure

## Phase 1-2 Directory Organization

```
yahoo_auction/
├── modules/                      # Main source code
│   ├── scraper/                  # Web スクレイピング機能
│   │   ├── rapras_scraper.py    # RaprasScraper クラス
│   │   ├── yahoo_scraper.py     # YahooAuctionScraper クラス
│   │   └── session_manager.py   # SessionManager クラス（Cookie管理）
│   ├── analyzer/                 # データ分析・処理機能
│   │   ├── product_analyzer.py  # ProductAnalyzer クラス（商品データ分析）
│   │   ├── seller_analyzer.py   # SellerAnalyzer クラス（セラー統計）
│   │   └── anime_filter.py      # AnimeFilter クラス（アニメ判定）
│   ├── storage/                  # データ永続化
│   │   ├── csv_exporter.py      # CSVExporter クラス
│   │   └── models.py            # データモデル（Product, Seller等）
│   ├── config/                   # 設定・環境変数
│   │   ├── settings.py          # 環境変数読み込み
│   │   └── constants.py         # 定数定義
│   └── utils/                    # ユーティリティ関数
│       └── logger.py            # ログ設定
│
├── tests/                        # テストコード
│   ├── test_scraper/
│   ├── test_analyzer/
│   ├── test_storage/
│   ├── fixtures/                 # モックデータ
│   └── integration/              # E2E テスト
│
├── main.py                       # CLI エントリーポイント
├── pyproject.toml
└── .spec-workflow/steering/      # ステアリング文書
```

## Naming Conventions

### Files

- **Modules**: `snake_case`（例：`rapras_scraper.py`、`product_analyzer.py`）
- **Test Files**: `test_*.py` または `*_test.py`（例：`test_rapras_scraper.py`）
- **Configuration Files**: `.env`、`settings.py`、`constants.py`
- **Directories**: `snake_case`（例：`modules/`、`tests/`）

### Code

- **Classes**: `PascalCase`（例：`RapraScraper`、`ProductAnalyzer`、`CSVExporter`）
- **Functions/Methods**: `snake_case`（例：`extract_product_title()`、`filter_sellers()`）
- **Constants**: `UPPER_SNAKE_CASE`（例：`MAX_RETRY_ATTEMPTS`、`TIMEOUT_SECONDS`）
- **Variables**: `snake_case`（例：`seller_name`、`product_list`）
- **Private Methods**: `_snake_case`（例：`_validate_input()`）

### Module Organization

1. Module docstring
2. Imports（標準ライブラリ → サードパーティ → ローカル）
3. Constants / Type definitions
4. Classes / Functions

## Import Patterns

- **絶対インポートのみ使用**（プロジェクトルートから）
- **Import順序**: 標準ライブラリ → サードパーティ → ローカル
- **禁止事項**: ワイルドカードインポート (`import *`)、相対インポート
- **自動整理**: `ruff check --fix` で統合

## Code Organization Principles

1. **Single Responsibility**: 各モジュールは1つの責務を持つ
   - `scraper/`: Web スクレイピング機能のみ
   - `analyzer/`: データ分析・処理のみ
   - `storage/`: データ永続化のみ

2. **Modularity**: 機能ごとに独立したモジュールに分割
   - `rapras_scraper.py` と `yahoo_scraper.py` は独立
   - `ProductAnalyzer` と `SellerAnalyzer` は分離

3. **Testability**: テストしやすい構造
   - 外部依存性は Constructor injection（コンストラクタ注入）
   - Mock 可能な設計

4. **Consistency**: 全モジュール共通パターンに従う

### Code Size Guidelines

#### ファイルサイズ

- **最大行数**: 500行程度
- **推奨**: 150-300行（平均）
- **超過時**: 機能分割を検討

#### 関数/メソッドサイズ

- **最大行数**: 50行
- **推奨**: 10-30行
- **ネスト深さ**: 3層まで

#### クラスサイズ

- **メソッド数**: 15個まで
- **行数**: 300行程度

## Module Boundaries & Dependencies

```
┌─────────────────────────┐
│      main.py (CLI)      │ ← エントリーポイント
└────────────┬────────────┘
             │
      ┌──────┴──────┐
      ▼             ▼
┌──────────────┐  ┌───────────────┐
│   Scraper    │  │   Analyzer    │
│  - Rapras    │  │ - Product     │
│  - Yahoo     │  │ - Seller      │
│  - Session   │  │ - Transformer │
└──────┬───────┘  └───────┬───────┘
       │                  │
       └──────────┬───────┘
                  ▼
           ┌─────────────┐
           │   Storage   │
           │  - CSV      │
           │  - Models   │
           └─────────────┘
```

### 依存関係ルール

- **Scraper**: 外部 API のみに依存
- **Analyzer**: Scraper の出力を処理
- **Storage**: Analyzer の結果を保存
- **Config/Utils**: 全モジュールから利用可能

## Module Responsibilities（Phase 1-2）

### modules/scraper/
**責務**: 外部サイトからのデータ取得・認証管理

- **RaprasScraper**: Raprasサイトへのログイン・セラー情報取得
  - `login(phone: str) -> bool`: 電話番号ログイン（SMS入力待機）
  - `fetch_seller_products(seller_id: str) -> list[dict]`: セラー商品一覧取得
- **YahooAuctionScraper**: Yahoo!オークションの商品詳細取得
  - `fetch_product_details(product_id: str) -> dict`: 商品詳細取得
- **SessionManager**: Cookie・セッション管理
  - `save_session(session_data: dict) -> None`: セッション保存
  - `load_session() -> dict`: セッション復元

### modules/analyzer/
**責務**: 取得データの加工・フィルタリング・統計分析

- **ProductAnalyzer**: 商品データ分析
  - `analyze_trends(products: list[dict]) -> dict`: 売れ筋傾向分析
  - `calculate_statistics(products: list[dict]) -> dict`: 統計値算出
- **SellerAnalyzer**: セラー分析
  - `compare_sellers(sellers: list[dict]) -> dict`: 競合比較
  - `rank_sellers(sellers: list[dict]) -> list[dict]`: セラーランキング
- **AnimeFilter**: アニメタイトル判定
  - `is_anime_title(title: str) -> bool`: Web検索APIでアニメ判定
  - `filter_anime_products(products: list[dict]) -> list[dict]`: フィルタリング実行

### modules/storage/
**責務**: データの永続化・モデル定義

- **CSVExporter**: CSV出力
  - `export_products(products: list[Product], filepath: str) -> None`: 商品CSV出力
  - `export_sellers(sellers: list[Seller], filepath: str) -> None`: セラーCSV出力
- **models.py**: データクラス定義
  - `Product`: 商品データモデル（title, price, seller_id等）
  - `Seller`: セラーデータモデル（name, product_count, avg_price等）

## Code Documentation Standards

- **Module Docstring**: モジュールの目的
- **Function Docstring**: Google Style（Args, Returns, Raises）
- **Type Hints**: 全関数に型注釈

## Testing Standards

### テストケース設計プロセス（必須遵守）

#### 1. テスト観点の表作成（実装前）

まず、以下の形式でテスト観点を整理します:

| テストID | 分類 | 入力値 | 期待結果 | 備考 |
|---------|------|--------|---------|------|
| T001 | 正常系 | 有効なセラーID | 商品リスト取得成功 | 主要シナリオ |
| T002 | 境界値 | 空文字列 | ValidationError | 最小値 |
| T003 | 境界値 | 1000文字 | ValidationError | 最大値超過 |
| T004 | 異常系 | None | TypeError | NULL入力 |
| T005 | 異常系 | 123 | TypeError | 不正な型 |
| T006 | 異常系 | 存在しないID | NotFoundError | データ不在 |
| T007 | 外部依存 | API接続失敗 | ConnectionError | ネットワークエラー |

#### 2. テストコード実装

各テストケースにGiven/When/Then形式のコメントを付与:

```python
def test_fetch_seller_products_with_valid_id():
    """T001: 正常系 - 有効なセラーIDで商品リスト取得"""
    # Given: 有効なセラーIDが提供される
    scraper = RaprasScraper()
    seller_id = "valid_seller_123"

    # When: 商品リストを取得する
    result = scraper.fetch_seller_products(seller_id)

    # Then: 商品リストが正常に返される
    assert isinstance(result, list)
    assert len(result) > 0
```

#### 3. 必須カバレッジ要件

- ✅ **正常系**: 主要な成功シナリオ（最低1つ）
- ✅ **異常系**: 正常系と同数以上（必須）
- ✅ **境界値**: 0, 最小, 最大, ±1, 空, NULL
- ✅ **不正な型・形式**: str/int/None/dict等の型違い
- ✅ **外部依存の失敗**: API/DB/ファイルシステムのエラー
- ✅ **例外検証**: 例外の種別とメッセージ内容を検証

```python
# 例外検証の例
with pytest.raises(ValidationError) as exc_info:
    scraper.fetch_seller_products("")
assert "Seller ID cannot be empty" in str(exc_info.value)
```

#### 4. 実行とカバレッジ確認

```bash
# テスト実行
pytest tests/test_scraper/test_rapras_scraper.py -v

# カバレッジ取得
pytest tests/test_scraper/test_rapras_scraper.py \
  --cov=modules/scraper/rapras_scraper \
  --cov-report=html \
  --cov-report=term-missing

# 目標: 分岐網羅率（Branch Coverage）100%
# 最低要件: 80%（tech.md参照）
```

### テスト設計チェックリスト

実装前に以下を確認:

- [ ] テスト観点表を作成したか
- [ ] 失敗系 ≥ 正常系か
- [ ] 境界値を全て網羅したか
- [ ] Given/When/Thenコメントを付与したか
- [ ] 例外の種別とメッセージを検証しているか
- [ ] 分岐網羅率100%を達成できる設計か

## Phase 3+（詳細は実装時に決定）

Web フロントエンド（React）、バックエンド（FastAPI）、データベース連携等の追加ディレクトリ構成を計画中。
