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

### 開発手法: TDD (Test-Driven Development)

**Red-Green-Refactor サイクルを厳守**

1. **Red**: 失敗するテストを先に書く
2. **Green**: 最小限のコードでテストを通す
3. **Refactor**: コードを整理・最適化

**テストコード修正禁止原則**

基本原則: テストコードの修正は禁止（テストは仕様を表す）

- テスト失敗 → 実装側を修正
- テストが間違っている → 作業停止してユーザーに確認

例外ケース:
- テスト追加・修正タスクを依頼された場合
- 構文エラー、仕様矛盾、API互換性問題がある場合
- ※例外ケースでも必ずユーザーに確認

**テストデータ依存禁止原則**

実装コードは、テストで使用される特定データ値（変数名、テーブル名等）への特別処理を禁止

問題点:
- 脆弱なテスト: テストデータ変更で実装が機能しなくなる
- 隠蔽された仕様: 特定データ名への特別処理が暗黙的になる
- 汎用性の欠如: 実運用環境で機能しない可能性

### 品質チェック手順（コミット前に必須実行）

1. **Code Formatting**: `black modules/ tests/`
2. **Linting & Import**: `ruff check --fix modules/ tests/`
3. **Unit Testing**: `pytest tests/ -v`（失敗時は必ず修正、テスト削除禁止）
4. **Coverage Check**: `pytest --cov=modules --cov-report=html`（80%以上必須）
5. **Security Scan**: `bandit -r modules/ tests/`（High警告は必ず対処）
6. **Dependency Audit**: `pip-audit`

### 品質要件（必須遵守）

- ❌ **テスト削除禁止**
- ✅ **カバレッジ80%必須**
- ✅ **全チェックパス後にコミット**

### Version Control & Collaboration

**Branching Strategy（Git Worktree使用）**
- **main**: 安定版（手動マージのみ）
- **develop**: 開発統合ブランチ
- **feature/***: 機能実装ブランチ（git worktreeで分離）

**Development Workflow（tmux並列実行推奨）**

1. **実装フェーズ（feature/* ブランチ）**
   - git worktree で feature ブランチ作成
   - TDD サイクル実行（Red → Green → Refactor）
   - 品質チェック → 修正 → コミット

2. **レビュー&PR作成**（`/rabbit-rocket`）
   - CodeRabbit CLI でコードレビュー（ローカル）
   - 重大問題を修正（最大2回反復）
   - Push → develop へ PR作成
   - GitHub上でCodeRabbit & Copilotが自動レビュー
   - **自動修正機能**:
     - レビュー変更要求 → `claude-auto-fix.yml` が自動修正
     - テスト失敗 → `claude-test-fix.yml` が自動修正
     - 修正後は自動コミット&Push

3. **PR監視&マージ**（`/party`）
   - PR ステータス定期確認
   - CI/CD パス後に自動マージ
   - develop ブランチ更新（git pull）
   - worktree 削除

**Commit Message Format（日本語）**
```
<簡潔なタイトル>

<詳細説明（箇条書き）>

Spec: <仕様書名>
Task: <タスク番号>
```

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
