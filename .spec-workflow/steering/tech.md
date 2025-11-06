# Technology Stack

## Project Type

Web スクレイピング機能と自動化ツール、データ処理を備えた Python ベースのデスクトップアプリケーション・バックエンドシステム。

## Core Technologies

### Primary Language(s)
- **Language**: Python 3.12+
- **Runtime**: CPython
- **Package Manager**: uv（uvtoolsによる仮想環境管理）
- **Environment Setup**: `.venv/` ローカル仮想環境

### Key Dependencies/Libraries

#### Web Scraping & Automation
- **Playwright**: スクレイピング、SMS認証対応
- **BeautifulSoup** (オプション): HTML解析

#### Authentication & Session Management
- **Cookie管理**: セッション永続化
- **Credentials Storage**: .env ファイル

#### Data Processing & Storage
- **Pandas**: データ加工・CSV エクスポート
- **CSV**: データ永続化フォーマット


### Application Architecture（Phase 1-2）
- **CLI Layer**: main.py
- **Scraping Layer**: Playwright ベース
- **Data Processing Layer**: Analyzer
- **Storage Layer**: CSV ファイル出力

### External Integrations（Phase 1-2）
- **Rapras** (https://www.rapras.jp)
- **Yahoo! Auctions**
  - **Proxy**: ヤフーオークションへのアクセスはプロキシ経由で実施
    - **URL**: `http://YOUR_PROXY_SERVER:PORT` または `http://user:pass@YOUR_PROXY_SERVER:PORT`（BASIC認証対応）
    - **環境変数**:
      - `PROXY_URL`: プロキシサーバーのURL（例：`http://proxy.example.com:3128`）
      - `PROXY_USERNAME`: BASIC認証用ユーザー名（省略可）
      - `PROXY_PASSWORD`: BASIC認証用パスワード（省略可）
    - **.env.example の設定例**:
      ```
      # プロキシサーバー設定（.envに実際の値を設定）
      PROXY_URL=http://proxy.example.com:3128
      PROXY_USERNAME=your_username
      PROXY_PASSWORD=your_password
      ```
    - 実際のプロキシ設定は内部ドキュメント、または `.env` ファイルで管理

## Development Environment

### Build & Development Tools
- **Package Management**: uv + pip

### Code Quality Tools
- **Formatting**: Black（自動フォーマット）
- **Linting & Import Management**: Ruff（スタイルチェック、import 整理含む）
- **Testing Framework**: pytest（実装予定）
- **Async Testing**: pytest-asyncio（async/await関数のテスト対応）
- **Test Coverage**: pytest-cov（カバレッジ率 80% 以上を必須維持）
- **Security**: bandit（コード脆弱性検査）、pip-audit（依存関係脆弱性検査）
- **Documentation**: Sphinx / MkDocs（計画中）

### 品質チェック手順（コード修正後は必須実行）

**実行順序を厳守してください。各ステップで問題が検出された場合は、次のステップに進む前に修正が必要です。**

1. **Code Formatting**: `black modules/ tests/`
   - 自動フォーマット適用（エラーなし想定）
2. **Linting & Import**: `ruff check --fix modules/ tests/`
   - 自動修正可能な問題を修正、手動対応が必要なエラーはここで対処
3. **Unit Testing**: `pytest tests/ -v`（または `make test`）
   - **失敗時は必ず修正**（テスト削除は禁止）
   - **Async Tests対応**: `pyproject.toml`に`asyncio_mode = auto`を設定し、pytest-asyncioプラグイン有効化
4. **Coverage Check**: `pytest --cov=modules --cov-report=html`
   - **カバレッジ80%以上必須**（未達時は追加テスト作成）
   - レポート: `htmlcov/index.html`
5. **Security Scan**: `bandit -r modules/ tests/`
   - 重大度Highの警告は必ず対処
6. **Dependency Audit**: `pip-audit`
   - 脆弱性検出時は依存関係更新
7. **Git Commit**: タスク完了ごとに関連ファイルをコミット
   - **関連ファイルごとにグループ化**: 機能単位でまとめてadd
   - **適切なコミットメッセージ**: 変更内容、関連要件、詳細説明を含める（日本語で記述）
   - **コミットフォーマット**:
     ```
     <簡潔なタイトル（日本語）>

     <詳細な説明（日本語）>
     - 主要機能/変更点
     - 関連する要件番号
     - 技術的詳細

     Spec: <仕様書名>
     Task: <タスク番号>
     Related: <要件番号>
     ```

### 品質要件（必須遵守）

- ❌ **テスト削除禁止**: カバレッジ達成のためのテスト削除は厳禁
- ✅ **カバレッジ80%必須**: 全コミットでこの基準を維持
- ✅ **手順順守必須**: 上記7ステップ(Git Commit含む)を全て実行してからタスク完了
- ✅ **エラーゼロ**: 全チェックをパスすることが必須
- ✅ **タスクごとにコミット**: 各タスク完了時に必ずgit commitを実行
- ✅ **適切なグループ化**: 関連ファイルをまとめてコミット（機能単位）

### Version Control & Collaboration
- **VCS**: Git
- **Branching Strategy**: main ブランチのみ
- **Commit Strategy**:
  - タスク単位でコミット（1タスク = 1〜複数コミット）
  - 関連ファイルをグループ化（例: モジュール実装、テスト、ドキュメント）
  - 品質チェック（Black, Ruff, pytest）通過後にコミット
  - コミットメッセージは詳細に記述（変更内容、要件番号、技術詳細）
- **Commit Message Format**:
  - 言語: 日本語で記述
  - タイトル: 簡潔な変更概要（50文字以内推奨）
  - 本文: 詳細説明（箇条書き推奨）
  - フッター: Spec（仕様書名）、Task（タスク番号）、Related（要件番号）、Co-Authored-By

### Testing Strategy
- **Unit Tests**: 個別モジュールテスト
- **Integration Tests**: Rapras・Yahoo Auctions 連携テスト
- **E2E Tests**: Playwright UI テスト
- **Coverage Target**: 80% 以上を必須維持

## Key Requirements（Phase 1-2）

### Performance
- **Scraping Speed**: 1セラーあたり 30秒以下
- **Processing Speed**: 1000行 CSV 処理を 5秒以内に

### Quality & Reliability
- **Test Coverage**: 80% 以上を必須維持
- **Parallel Processing**: 複数セラー並行処理（計画中 — 現状未実装、将来実装予定）

### Security
- **Authentication**: SMS 認証対応
- **Credential Management**: .env ファイル管理

## Phase 3+（詳細は実装時に決定）

データベース連携、AI チャット、Web ダッシュボード等の拡張を計画中。
