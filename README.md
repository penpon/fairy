# Yahoo Auction Scraper with Rapras Authentication

ラプラス（Rapras）とヤフーオークション（Yahoo Auctions）への認証を自動化するPythonスクレイパー。SMS認証コードの入力を半自動化し、セッション情報をCookieで永続化することで、毎回のログイン作業を削減します。

## 機能

- **Rapras認証**: ユーザー名・パスワードによる自動ログイン
- **Yahoo Auctions認証**: 電話番号・SMS認証（プロキシBASIC認証経由）
- **セッション永続化**: Cookie保存による再利用
- **エラーハンドリング**: 自動リトライ（最大3回、指数バックオフ）
- **タイムアウト処理**: 30秒のネットワークタイムアウト

## 必要要件

- Python 3.12以上
- uv（Python環境管理ツール）
- Playwright（ブラウザ自動化）

## セットアップ

### 1. 仮想環境の作成とインストール

```bash
# 仮想環境を作成
uv venv

# 依存関係をインストール
uv pip install -e ".[dev]"

# Playwrightブラウザをインストール
.venv/bin/playwright install chromium
```

### 2. 環境変数の設定

`.env.example`をコピーして`.env`ファイルを作成し、認証情報を設定します。

```bash
cp .env.example .env
```

`.env`ファイルを編集して、以下の情報を設定してください：

```env
# Rapras認証情報
RAPRAS_USERNAME=your_rapras_username
RAPRAS_PASSWORD=your_rapras_password

# Yahoo Auctions認証情報
YAHOO_PHONE_NUMBER=09012345678

# プロキシ設定（Yahoo Auctions用）
PROXY_URL=http://164.70.96.2:3128
PROXY_USERNAME=your_proxy_username
PROXY_PASSWORD=your_proxy_password
```

**セキュリティ注意**: `.env`ファイルは絶対にGitにコミットしないでください。

## 使用方法

### Raprasへのログイン

```python
import asyncio
from modules.scraper.rapras_scraper import RaprasScraper
from modules.scraper.session_manager import SessionManager
from modules.config.settings import load_rapras_config

async def main():
    # 設定を読み込み
    config = load_rapras_config()

    # SessionManagerを作成
    session_manager = SessionManager()

    # RaprasScraperを作成
    scraper = RaprasScraper(session_manager=session_manager)

    try:
        # ログイン
        success = await scraper.login(config.username, config.password)

        if success:
            print("ログインに成功しました")
        else:
            print("ログインに失敗しました")
    finally:
        await scraper.close()

# 実行
asyncio.run(main())
```

### Yahoo Auctionsへのログイン（SMS認証）

```python
import asyncio
from modules.scraper.yahoo_scraper import YahooAuctionScraper
from modules.scraper.session_manager import SessionManager
from modules.config.settings import load_yahoo_config, load_proxy_config

async def main():
    # 設定を読み込み
    yahoo_config = load_yahoo_config()
    proxy_config = load_proxy_config()

    # SessionManagerを作成
    session_manager = SessionManager()

    # プロキシ設定をdict形式に変換
    proxy_dict = {
        "url": proxy_config.url,
        "username": proxy_config.username,
        "password": proxy_config.password
    }

    # YahooAuctionScraperを作成
    scraper = YahooAuctionScraper(
        session_manager=session_manager,
        proxy_config=proxy_dict
    )

    try:
        # ログイン（SMS認証コードの入力が必要）
        success = await scraper.login(yahoo_config.phone_number)

        if success:
            print("ログインに成功しました")
        else:
            print("ログインに失敗しました")
    finally:
        await scraper.close()

# 実行
asyncio.run(main())
```

**SMS認証の流れ**:
1. 電話番号が自動入力されます
2. SMS送信ボタンがクリックされます
3. コンソールにプロンプトが表示されます: `SMS認証コード: `
4. スマートフォンに届いたSMS認証コードを入力してください
5. タイムアウト: 3分

## テスト

### 全テストの実行

```bash
.venv/bin/pytest -v
```

### カバレッジレポート付きでテスト実行

```bash
.venv/bin/pytest --cov=modules --cov-report=html --cov-report=term-missing
```

カバレッジレポートは`htmlcov/index.html`で確認できます。

### 統合テストをスキップしてユニットテストのみ実行

```bash
.venv/bin/pytest -v -m "not integration"
```

## コード品質チェック

### フォーマットチェック（Black）

```bash
.venv/bin/black modules/ tests/ --check
```

### フォーマット適用

```bash
.venv/bin/black modules/ tests/
```

### リントチェック（Ruff）

```bash
.venv/bin/ruff check modules/ tests/
```

### リントエラーの自動修正

```bash
.venv/bin/ruff check modules/ tests/ --fix
```

## プロジェクト構造

```
.
├── modules/
│   ├── scraper/
│   │   ├── rapras_scraper.py       # Rapras認証スクレイパー
│   │   ├── yahoo_scraper.py        # Yahoo Auctions認証スクレイパー
│   │   └── session_manager.py      # セッション管理（Cookie永続化）
│   ├── config/
│   │   └── settings.py             # 環境変数管理
│   └── utils/
│       └── logger.py               # ログ設定
├── tests/
│   ├── test_scraper/
│   │   ├── test_session_manager.py
│   │   ├── test_rapras_scraper.py
│   │   └── test_yahoo_scraper.py
│   ├── test_config/
│   │   └── test_settings.py
│   └── test_utils/
│       └── test_logger.py
├── sessions/                       # セッションファイル保存ディレクトリ（自動生成）
├── .env                            # 環境変数ファイル（要作成、Gitにコミットしない）
├── .env.example                    # 環境変数テンプレート
├── pyproject.toml                  # プロジェクト設定
├── pytest.ini                      # pytest設定
└── README.md                       # このファイル
```

## トラブルシューティング

### Playwrightブラウザが見つからない

```bash
.venv/bin/playwright install chromium
```

### プロキシ認証エラー

`.env`ファイルの`PROXY_USERNAME`と`PROXY_PASSWORD`が正しいか確認してください。

### セッションファイルが破損している

セッションファイルを削除して再度ログインしてください：

```bash
rm -rf sessions/
```

### SMS認証コード入力タイムアウト

タイムアウトは3分です。時間内にSMS認証コードを入力してください。

## ライセンス

このプロジェクトは内部使用のみを目的としています。

## 貢献

バグ報告や機能リクエストは、プロジェクトの課題トラッカーに投稿してください。
