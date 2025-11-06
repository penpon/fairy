# 統合テスト (Integration Tests)

このディレクトリには、Yahoo Auction Scraperの統合テスト（E2Eテスト）が含まれています。

## 概要

統合テストは、実際のPlaywrightブラウザを使用して、完全な認証フローをテストします：

1. **Raprasログイン** → セッション保存
2. **Yahoo Auctionsログイン**（プロキシ + SMS認証） → セッション保存
3. **セッション復元** → ログインスキップ

## セットアップ

### 1. 環境変数の設定

プロジェクトルートに `.env` ファイルを作成し、以下の認証情報を設定してください：

```bash
# Rapras認証情報
RAPRAS_USERNAME=your_rapras_username
RAPRAS_PASSWORD=your_rapras_password

# Yahoo Auctions認証情報
YAHOO_PHONE_NUMBER=09012345678

# プロキシ設定（BASIC認証）
PROXY_URL=http://164.70.96.2:3128
PROXY_USERNAME=your_proxy_username
PROXY_PASSWORD=your_proxy_password
```

**重要**: `.env` ファイルは `.gitignore` に含まれており、Gitにコミットされません。

### 2. Playwrightブラウザのインストール

統合テストを実行する前に、Playwrightブラウザをインストールしてください：

```bash
playwright install chromium
```

## テストの実行

### 統合テストのみを実行

```bash
pytest -m integration -v
```

### 統合テストを除外して実行

```bash
pytest -m "not integration" -v
```

### 全てのテストを実行（ユニット + 統合）

```bash
pytest -v
```

### 特定の統合テストクラスを実行

```bash
# Rapras認証フローのみ
pytest tests/integration/test_authentication_flow.py::TestRaprasAuthenticationFlow -v

# Yahoo Auctions認証フローのみ
pytest tests/integration/test_authentication_flow.py::TestYahooAuctionsAuthenticationFlow -v

# 完全な認証フロー
pytest tests/integration/test_authentication_flow.py::TestCompleteAuthenticationFlow -v
```

### 特定のテストメソッドを実行

```bash
# Raprasログインテスト
pytest tests/integration/test_authentication_flow.py::TestRaprasAuthenticationFlow::test_rapras_login_and_session_save -v

# Yahoo Auctionsログインテスト（SMS入力が必要）
pytest tests/integration/test_authentication_flow.py::TestYahooAuctionsAuthenticationFlow::test_yahoo_login_with_proxy_and_sms -v
```

## テスト実行時の注意事項

### SMS認証コード入力

Yahoo Auctionsログインテストでは、**手動でSMS認証コードを入力する必要があります**：

1. テスト実行中に、スマートフォンでSMSを受信
2. ターミナルにプロンプトが表示されるので、受信したコードを入力
3. タイムアウト: **3分**

```
==================================================
SMS認証コードを入力してください
タイムアウト: 3分
==================================================
SMS認証コード: [ここに6桁のコードを入力]
```

### セッション復元テスト

セッション復元テスト (`test_rapras_session_restoration`, `test_yahoo_session_restoration`) を実行する前に、
対応するログインテストを実行してセッションファイルを作成してください：

```bash
# 順序1: ログインテスト（セッション作成）
pytest tests/integration/test_authentication_flow.py::TestRaprasAuthenticationFlow::test_rapras_login_and_session_save -v

# 順序2: セッション復元テスト（SMS入力不要）
pytest tests/integration/test_authentication_flow.py::TestRaprasAuthenticationFlow::test_rapras_session_restoration -v
```

### 完全なフローテスト

完全な認証フローテスト (`test_complete_authentication_flow`) は、Rapras → Yahoo Auctionsの両方のログインを実行します：

```bash
pytest tests/integration/test_authentication_flow.py::TestCompleteAuthenticationFlow::test_complete_authentication_flow -v
```

このテストは**SMS入力が必要**です。

完全なセッション復元フローテスト (`test_complete_session_restoration_flow`) を実行する前に、
`test_complete_authentication_flow` を実行してセッションファイルを作成してください。

## CI/CD環境での実行

CI/CD環境（GitHub Actionsなど）では、手動SMS入力が不可能なため、統合テストをスキップすることを推奨します：

```yaml
# GitHub Actionsの例
- name: Run tests (skip integration)
  run: pytest -m "not integration" --cov=modules --cov-report=xml
```

ローカル環境でのみ統合テストを実行し、本番デプロイ前に動作を確認してください。

## テストの独立性

各統合テストは独立して実行可能です：

- テスト用の一時セッションディレクトリ (`tmp_path / "test_sessions"`) を使用
- テスト終了後、セッションファイルは自動的に削除される
- テスト間でセッションが干渉しない

## トラブルシューティング

### `Config not available` エラー

`.env` ファイルに必要な環境変数が設定されていない場合、テストはスキップされます：

```
SKIPPED [1] Config not available: RAPRAS_USERNAME not found
```

→ `.env` ファイルを確認し、必要な環境変数を設定してください。

### `Playwright browsers not installed` エラー

Playwrightブラウザがインストールされていない場合：

```bash
playwright install chromium
```

### `Proxy authentication failed` エラー

プロキシBASIC認証の認証情報が誤っている可能性があります：

- `.env` ファイルの `PROXY_USERNAME` と `PROXY_PASSWORD` を確認
- プロキシサーバー `http://164.70.96.2:3128` が稼働していることを確認

### SMS入力タイムアウト

3分以内にSMS認証コードを入力できなかった場合、テストは失敗します：

```
TimeoutError: SMS code input timeout. Please try again.
```

→ テストを再実行し、SMSを素早く入力してください。

## セキュリティ注意事項

- **認証情報を絶対にコミットしないでください**
- `.env` ファイルは `.gitignore` に含まれています
- セッションファイルもGitにコミットされません
- ログには認証情報が記録されません（電話番号、パスワードなど）

## テスト対象

| テストクラス | テストメソッド | 説明 | SMS入力 |
|------------|--------------|------|---------|
| `TestRaprasAuthenticationFlow` | `test_rapras_login_and_session_save` | Raprasログイン → セッション保存 | 不要 |
| `TestRaprasAuthenticationFlow` | `test_rapras_session_restoration` | Raprasセッション復元 | 不要 |
| `TestYahooAuctionsAuthenticationFlow` | `test_yahoo_login_with_proxy_and_sms` | Yahoo Auctionsログイン（プロキシ + SMS） | **必要** |
| `TestYahooAuctionsAuthenticationFlow` | `test_yahoo_session_restoration` | Yahoo Auctionsセッション復元 | 不要 |
| `TestCompleteAuthenticationFlow` | `test_complete_authentication_flow` | 完全な認証フロー（Rapras → Yahoo） | **必要** |
| `TestCompleteAuthenticationFlow` | `test_complete_session_restoration_flow` | 完全なセッション復元フロー | 不要 |

## まとめ

統合テストは、実際の認証フローが正しく動作することを確認するための重要なテストです。
ローカル環境で定期的に実行し、認証機能の信頼性を確保してください。

**推奨実行順序**:
1. `test_rapras_login_and_session_save` → `test_rapras_session_restoration`
2. `test_yahoo_login_with_proxy_and_sms` (SMS入力) → `test_yahoo_session_restoration`
3. `test_complete_authentication_flow` (SMS入力) → `test_complete_session_restoration_flow`
