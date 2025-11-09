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
- **Testing Framework**: pytest
- **Async Testing**: pytest-asyncio（async/await関数のテスト対応）
- **Test Coverage**: pytest-cov（カバレッジ率 95% 以上を必須維持）
- **Security**: bandit（コード脆弱性検査）、pip-audit（依存関係脆弱性検査）
- **Documentation**: Sphinx / MkDocs（計画中）

### 開発手法

**TDD (Test-Driven Development)**: `/tdd-cycle` コマンドでRed-Green-Refactorサイクルを実行

**品質管理**: `/quality-check` コマンドでコミット前チェック（カバレッジ95%必須）

### Version Control & Collaboration

**Branching Strategy（Git Worktree使用）**
- **main**: 安定版（手動マージのみ）
- **develop**: 開発統合ブランチ
- **feature/***: 機能実装ブランチ（git worktreeで分離）

**Development Workflow（tmux並列実行推奨）**

1. **実装フェーズ（feature/* ブランチ）**
   - git worktree で feature ブランチ作成
   - `/tdd-cycle` でTDD実装（Red → Green → Refactor → QC → Log → Commit）
     - TDDサイクルが強制され、確実にテストファーストで実装
     - 品質チェック（`/quality-check`）が自動実行される

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

**ワークフロー チェックリスト（参考）**

タスク実装サイクル:
- [ ] 1. git worktree でfeatureブランチ作成
- [ ] 2. `/tdd-cycle` でTDD実装
- [ ] 3. `/rabbit-rocket` でレビュー&PR作成
- [ ] 4. GitHub自動レビュー（CodeRabbit/Copilot）
- [ ] 5. GitHub自動修正（必要時）
- [ ] 6. `/party` でPR監視&マージ
- [ ] 7. 全タスク完了後、developをmainにマージ（手動）

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
- **Coverage Target**: 95% 以上を必須維持

## Key Requirements（Phase 1-2）

### Performance
- **Scraping Speed**: 1セラーあたり 30秒以下
- **Processing Speed**: 1000行 CSV 処理を 5秒以内に

### Quality & Reliability
- **Test Coverage**: 95% 以上を必須維持

### Security
- **Authentication**: SMS 認証対応
- **Credential Management**: .env ファイル管理

## Phase 3+（詳細は実装時に決定）

以下の拡張機能を計画中：
- データベース連携
- AI チャット
- Web ダッシュボード
- **Parallel Processing**: 複数セラー並行処理
