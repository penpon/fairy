# Requirements Document

## Introduction

ラプラス（Rapras）とヤフーオークションへの認証を自動化する機能です。SMS認証コードの入力を半自動化し、セッション情報をCookieで永続化することで、ユーザーが毎回ログイン情報を入力する手間を削減します。この機能は、セラーデータ収集機能の前提条件となる重要な基盤機能です。

## Alignment with Product Vision

本機能は、product.mdで定義されている「ラプラス・ヤフーオークション認証自動化（SMS半自動対応）」を実現します。認証の自動化により、以下の価値を提供します：

- **作業効率化**: ログイン作業を自動化し、ユーザーの手間を最小限に抑制
- **セキュリティ**: SMS認証を維持しながら、セッション永続化で安全性を確保
- **信頼性**: Connection Success Rate 100%を達成（Critical Success Criteria準拠）

## Requirements

### Requirement 1: Raprasユーザー名・パスワード認証

**User Story:** ヤフーオークション出品者として、Raprasサイト（https://www.rapras.jp/）にユーザー名とパスワードでログインしたいので、自動的に認証を完了できるようにしたい

#### Acceptance Criteria

1. WHEN ユーザーがユーザー名とパスワードを.envファイルに設定 THEN システムは環境変数から認証情報を読み込む
2. WHEN システムがRaprasログインページ（https://www.rapras.jp/）にアクセス THEN システムはユーザー名とパスワードを入力フォームに自動入力する
3. WHEN ログインボタンをクリック THEN システムはログイン成功/失敗を判定する
4. IF ログインに成功 THEN システムはセッションCookieを保存し、ログイン完了メッセージを表示する
5. IF ログインに失敗 THEN システムはエラーメッセージを表示し、再試行を促す
6. WHEN ログイン試行が3回失敗 THEN システムは処理を中断し、エラーログを記録する

### Requirement 2: Yahoo Auctions電話番号・SMS認証（プロキシ経由）

**User Story:** ヤフーオークション出品者として、Yahoo Auctionsサイト（https://auctions.yahoo.co.jp/）に電話番号でログインしたいので、手元のスマートフォンでSMSコードを受信し、PCで入力してログインを完了できるようにしたい

#### Acceptance Criteria

1. WHEN システムがYahoo Auctions（https://auctions.yahoo.co.jp/）にアクセス THEN システムはBASIC認証付きプロキシサーバー（環境変数`PROXY_URL`で設定。例：http://host:port）経由で接続する
2. WHEN プロキシ接続を確立 THEN システムはBASIC認証の認証情報（ユーザー名・パスワード）を.envファイルから読み込み、プロキシサーバーに送信する
3. IF プロキシ認証が失敗 THEN システムはProxyAuthenticationErrorを発生させ、エラーログを記録する
4. WHEN システムがYahoo Auctionsログインページにアクセス THEN システムは電話番号を.envファイルから読み込み、入力フォームに自動入力する
5. WHEN Yahoo Auctionsが電話番号を送信 THEN システムはSMS送信完了を検知し、ユーザーにSMSコード入力を促すメッセージを表示する
6. WHEN ユーザーがSMSコードを入力 THEN システムは認証コードをYahoo Auctionsに送信し、ログイン成功/失敗を判定する
7. IF ログインに成功 THEN システムはセッションCookieを保存し、ログイン完了メッセージを表示する
8. IF ログインに失敗 THEN システムはエラーメッセージを表示し、再試行を促す

### Requirement 3: セッション永続化

**User Story:** ヤフーオークション出品者として、毎回ログイン情報を入力せずに済むように、セッション情報を安全に保存・復元できるようにしたい

#### Acceptance Criteria

1. WHEN RaprasまたはYahoo Auctionsログインに成功 THEN システムは各サービスのセッションCookieをローカルファイルに保存する
2. WHEN 次回起動時 THEN システムは保存されたセッションCookieを読み込み、ログイン処理をスキップする
3. IF セッションが有効期限切れ THEN システムは再ログインを実行し、新しいセッションを保存する
   - **有効期限検出戦略**：
     - ステップ1（プロアクティブ）：クッキー属性（Expires/Max-Age）をチェック
     - ステップ2（軽量プローブ）：各サービスの検証エンドポイントで軽量リクエストを実行
     - ステップ3（リアクティブ）：特定のHTTPステータスコード（401/403など）を有効期限切れとして扱う
     - 優先順位：クッキーメタデータ > APIプローブ > HTTPレスポンスコード
     - 期限切れ時は401/403エラー、または有効期限切れ専用の例外を発生
4. WHEN セッションファイルが破損または存在しない THEN システムは新規ログインプロセスを開始する
5. IF セッション保存に失敗 THEN システムは警告ログを記録するが、処理は継続する

### Requirement 4: エラーハンドリングとリトライ

**User Story:** ヤフーオークション出品者として、一時的なネットワークエラーで処理が失敗しても、自動的にリトライされることで安定した動作を期待したい

#### Acceptance Criteria

1. WHEN ネットワーク接続エラーが発生 THEN システムは最大3回まで自動リトライする（指数バックオフ: 2秒, 4秒, 8秒）
2. WHEN タイムアウトが発生（30秒超過）THEN システムはTimeoutErrorを発生させ、リトライを実行する
3. IF 3回のリトライが全て失敗 THEN システムは処理を中断し、詳細なエラーログを記録する
4. WHEN HTTPステータスコードが5xx系 THEN システムはサーバーエラーとして扱い、リトライを実行する
5. IF HTTPステータスコードが4xx系 THEN システムはクライアントエラーとして扱い、リトライせずに例外を発生させる

## Non-Functional Requirements

### Code Architecture and Modularity
- **Single Responsibility Principle**: 認証機能は`modules/scraper/`配下に配置し、RaprasScraperクラスとSessionManagerクラスで責務を分離
- **Modular Design**: 認証ロジック、セッション管理、プロキシ設定を独立したモジュールとして実装
- **Dependency Management**: Playwrightへの依存を最小化し、テスト時にモック可能な設計
- **Clear Interfaces**: 公開メソッド（login, save_session, load_session）と内部メソッド（_validate_phone, _retry_connection）を明確に分離

### Performance
- **Connection Success Rate**: 100%（product.md Critical Success Criteria準拠）
- **Login Time**: 初回ログイン30秒以内、セッション復元時5秒以内
- **Timeout**: ネットワーク接続タイムアウト30秒
- **Retry Delay**: 指数バックオフ（2秒, 4秒, 8秒）

### Security
- **Credential Management**:
  - Rapras: ユーザー名・パスワードは.envファイルから読み込み、ハードコーディング禁止
  - Yahoo Auctions: 電話番号は.envファイルから読み込み、ハードコーディング禁止
  - プロキシBASIC認証: ユーザー名・パスワードは.envファイルから読み込み
- **Session Storage**: セッションCookieはローカルファイルに**暗号化して保存**（AES-GCM等の認証付き対称暗号化を必須）
  - 暗号化キーはOS提供のキーチェーン、またはセキュアなシークレット管理ツールで管理（ハードコード禁止）
  - プレーンテキストのセッショントークンはディスクに書き込まない
  - 暗号化と鍵管理の実装を自動テストで検証
- **Proxy Security**: プロキシサーバーのURL・BASIC認証情報は.envファイルで管理
- **Error Logging**: エラーログにはセンシティブ情報（電話番号、パスワード、認証情報）を含めない

### Reliability
- **Error Handling**: 全ての外部API呼び出しにはtry-except処理を実装
- **Retry Strategy**: 一時的なネットワークエラーに対して最大3回リトライ
- **Session Validation**: セッションロード時に有効期限を検証
- **Graceful Degradation**: セッション保存失敗時も処理を継続

### Usability
- **User Feedback**: SMS認証コード入力時に明確なプロンプトを表示
- **Error Messages**: ユーザーフレンドリーなエラーメッセージ（日本語）
- **Logging**: INFO/WARNING/ERRORレベルでのログ出力（modules/utils/logger.py使用）

### Testability
- **Test Coverage**: 90%以上（tech.md準拠）
- **Unit Tests**: 各メソッドの正常系・異常系・境界値テスト
- **Integration Tests**: Rapras/Yahoo Auctions実環境テスト
- **Mock Support**: Playwright操作をモック可能な設計
