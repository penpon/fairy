# Tasks Document

- [x] 1. SessionManagerクラスの実装
  - File: modules/scraper/session_manager.py
  - Cookie永続化・復元機能を実装
  - save_session、load_session、session_exists、delete_sessionメソッドを実装
  - Purpose: セッション管理の基盤機能を提供
  - _Leverage: json（標準ライブラリ）、pathlib（標準ライブラリ）_
  - _Requirements: Requirement 3（セッション永続化）_
  - _Prompt: Implement the task for spec rapras-yahoo-authentication, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer specializing in file I/O and JSON serialization | Task: Create SessionManager class in modules/scraper/session_manager.py following Requirement 3 (セッション永続化), implementing save_session, load_session, session_exists, and delete_session methods using json and pathlib libraries | Restrictions: Do not hardcode file paths, handle JSONDecodeError gracefully with warning logs, ensure directory creation if not exists, do not expose sensitive data in logs | Success: All methods work correctly with proper error handling, session files are created in sessions/ directory, corrupted JSON files return None with warning log, tests achieve 80%+ coverage | Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md. After completing implementation and tests, mark as completed ([x]) in tasks.md._

- [x] 2. Settings（環境変数管理）の実装
  - File: modules/config/settings.py
  - RaprasConfig、YahooConfig、ProxyConfigのデータクラスを定義
  - load_rapras_config、load_yahoo_config、load_proxy_configを実装
  - Purpose: .envファイルから認証情報を読み込む
  - _Leverage: os（標準ライブラリ）、dataclasses（標準ライブラリ）_
  - _Requirements: Requirement 1（Rapras認証）、Requirement 2（Yahoo Auctions認証）_
  - _Prompt: Implement the task for spec rapras-yahoo-authentication, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer with expertise in environment variable management and dataclasses | Task: Create configuration management in modules/config/settings.py following Requirements 1 and 2, defining RaprasConfig, YahooConfig, and ProxyConfig dataclasses with load functions that read from environment variables using os module | Restrictions: Do not use hardcoded values, raise clear exceptions when required env vars are missing, do not log sensitive values, follow dataclass patterns | Success: All config classes are properly defined, load functions correctly read from .env, missing env vars raise descriptive exceptions, tests achieve 80%+ coverage | Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md. After completing implementation and tests, mark as completed ([x]) in tasks.md._

- [x] 3. Logger（ログ設定）の実装
  - File: modules/utils/logger.py
  - get_logger関数を実装（INFO/WARNING/ERRORレベル）
  - Purpose: 統一されたログ出力を提供
  - _Leverage: logging（標準ライブラリ）_
  - _Requirements: Non-Functional Requirements（Usability - Logging）_
  - _Prompt: Implement the task for spec rapras-yahoo-authentication, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer with expertise in logging configuration and best practices | Task: Create logging utility in modules/utils/logger.py following Non-Functional Requirements (Usability - Logging), implementing get_logger function that returns configured logger with INFO/WARNING/ERROR levels using Python's logging module | Restrictions: Do not log sensitive information (passwords, phone numbers), use appropriate log levels, ensure log format includes timestamp and module name, do not create multiple handlers | Success: get_logger returns properly configured logger, log format is consistent and readable, no sensitive data in logs, tests verify correct logging behavior | Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md. After completing implementation and tests, mark as completed ([x]) in tasks.md._

- [x] 4. RaprasScraperクラスの実装
  - File: modules/scraper/rapras_scraper.py
  - Playwrightを使用したRapras認証の自動化
  - login、is_logged_in、closeメソッドを実装
  - Purpose: Raprasサイトへの自動ログイン機能を提供
  - _Leverage: modules/scraper/session_manager.py、modules/config/settings.py、modules/utils/logger.py、Playwright_
  - _Requirements: Requirement 1（Raprasユーザー名・パスワード認証）、Requirement 4（エラーハンドリングとリトライ）_
  - _Prompt: Implement the task for spec rapras-yahoo-authentication, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer specializing in web scraping and browser automation with Playwright | Task: Create RaprasScraper class in modules/scraper/rapras_scraper.py following Requirements 1 and 4, implementing login (username/password authentication to https://www.rapras.jp/), is_logged_in, and close methods using Playwright with SessionManager for cookie persistence | Restrictions: Do not hardcode URLs or credentials, implement retry logic (max 3 attempts with exponential backoff: 2s, 4s, 8s), handle TimeoutError (30s timeout), use SessionManager for cookie management, do not bypass error handling | Success: Login succeeds with valid credentials, session cookies are saved via SessionManager, retry logic works on network errors, timeout is enforced at 30s, tests with mocked Playwright achieve 80%+ coverage | Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md. After completing implementation and tests, mark as completed ([x]) in tasks.md._

- [x] 5. YahooAuctionScraperクラスの実装
  - File: modules/scraper/yahoo_scraper.py
  - Playwrightを使用したYahoo Auctions認証の自動化（プロキシBASIC認証経由）
  - login、is_logged_in、closeメソッドを実装
  - Purpose: Yahoo Auctionsサイトへの自動ログイン機能を提供（SMS認証半自動対応）
  - _Leverage: modules/scraper/session_manager.py、modules/config/settings.py、modules/utils/logger.py、Playwright_
  - _Requirements: Requirement 2（Yahoo Auctions電話番号・SMS認証）、Requirement 4（エラーハンドリングとリトライ）_
  - _Prompt: Implement the task for spec rapras-yahoo-authentication, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Developer specializing in web scraping, proxy configuration, and SMS authentication flows | Task: Create YahooAuctionScraper class in modules/scraper/yahoo_scraper.py following Requirements 2 and 4, implementing login (phone number + SMS authentication to https://auctions.yahoo.co.jp/ via BASIC auth proxy http://164.70.96.2:3128), is_logged_in, and close methods using Playwright with proxy configuration | Restrictions: Must configure proxy with BASIC authentication (username/password from .env), implement retry logic (max 3 attempts), handle ProxyAuthenticationError separately (no retry), prompt user for SMS code input (max 3 min timeout), handle TimeoutError (30s timeout), use SessionManager for cookies, do not log proxy credentials | Success: Proxy connection works with BASIC auth, phone number auto-fills from .env, user is prompted for SMS code, login succeeds after SMS verification, session cookies saved via SessionManager, ProxyAuthenticationError raised on auth failure, tests with mocked Playwright achieve 80%+ coverage | Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md. After completing implementation and tests, mark as completed ([x]) in tasks.md._

- [x] 6. SessionManager ユニットテストの実装
  - File: tests/test_scraper/test_session_manager.py
  - save_session、load_session、session_exists、delete_sessionのテストを実装
  - 正常系・異常系・境界値テストを網羅
  - Purpose: SessionManagerの信頼性を確保
  - _Leverage: pytest、pytest-mock、modules/scraper/session_manager.py_
  - _Requirements: Requirement 3（セッション永続化）_
  - _Prompt: Implement the task for spec rapras-yahoo-authentication, first run spec-workflow-guide to get the workflow guide then implement the task: Role: QA Engineer with expertise in pytest and file I/O testing | Task: Create comprehensive unit tests for SessionManager in tests/test_scraper/test_session_manager.py following Requirement 3, covering save_session, load_session, session_exists, and delete_session methods with success, error, and edge cases | Restrictions: Must test both success and failure scenarios, test JSON corruption handling, test file not found scenarios, use Given/When/Then comments, verify warning logs for errors, achieve 80%+ coverage, do not test external dependencies directly | Success: All SessionManager methods tested, JSON corruption returns None with warning, file operations work correctly, edge cases (empty cookies, missing directory) covered, tests run independently, 80%+ coverage achieved | Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md. After completing implementation, mark as completed ([x]) in tasks.md._

- [x] 7. Settings ユニットテストの実装
  - File: tests/test_config/test_settings.py
  - load_rapras_config、load_yahoo_config、load_proxy_configのテストを実装
  - 環境変数不在時の例外テストを含む
  - Purpose: 環境変数管理の信頼性を確保
  - _Leverage: pytest、pytest-mock、modules/config/settings.py_
  - _Requirements: Requirement 1（Rapras認証）、Requirement 2（Yahoo Auctions認証）_
  - _Prompt: Implement the task for spec rapras-yahoo-authentication, first run spec-workflow-guide to get the workflow guide then implement the task: Role: QA Engineer with expertise in pytest and environment variable testing | Task: Create comprehensive unit tests for Settings in tests/test_config/test_settings.py following Requirements 1 and 2, covering all load functions with valid env vars, missing env vars, and edge cases | Restrictions: Must mock environment variables using pytest-mock, test missing env var exceptions with descriptive messages, use Given/When/Then comments, achieve 80%+ coverage, ensure test isolation | Success: All load functions tested with valid and invalid env vars, exceptions are descriptive, dataclass creation works correctly, tests run independently, 80%+ coverage achieved | Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md. After completing implementation, mark as completed ([x]) in tasks.md._

- [x] 8. RaprasScraper ユニットテストの実装
  - File: tests/test_scraper/test_rapras_scraper.py
  - login、is_logged_in、closeメソッドのテストを実装（Playwrightモック使用）
  - リトライロジック、タイムアウト処理のテストを含む
  - Purpose: RaprasScraper の信頼性を確保
  - _Leverage: pytest、pytest-asyncio、pytest-mock、modules/scraper/rapras_scraper.py_
  - _Requirements: Requirement 1（Rapras認証）、Requirement 4（エラーハンドリングとリトライ）_
  - _Prompt: Implement the task for spec rapras-yahoo-authentication, first run spec-workflow-guide to get the workflow guide then implement the task: Role: QA Engineer with expertise in pytest-asyncio and mocking Playwright | Task: Create comprehensive unit tests for RaprasScraper in tests/test_scraper/test_rapras_scraper.py following Requirements 1 and 4, mocking Playwright to test login success, login failure, retry logic (max 3 attempts with exponential backoff), timeout handling (30s), and session cookie saving | Restrictions: Must mock Playwright completely, test retry logic with network errors, verify exponential backoff timing, test timeout exceptions, verify SessionManager.save_session is called, use Given/When/Then comments, achieve 80%+ coverage | Success: Login success/failure scenarios tested, retry logic works correctly (3 attempts max), exponential backoff verified (2s, 4s, 8s), timeout enforced at 30s, session cookies saved on success, tests run independently, 80%+ coverage achieved | Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md. After completing implementation, mark as completed ([x]) in tasks.md._

- [x] 9. YahooAuctionScraper ユニットテストの実装
  - File: tests/test_scraper/test_yahoo_scraper.py
  - login、is_logged_in、closeメソッドのテストを実装（Playwrightモック使用）
  - プロキシ認証、SMS入力、リトライロジックのテストを含む
  - Purpose: YahooAuctionScraperの信頼性を確保
  - _Leverage: pytest、pytest-asyncio、pytest-mock、modules/scraper/yahoo_scraper.py_
  - _Requirements: Requirement 2（Yahoo Auctions認証）、Requirement 4（エラーハンドリングとリトライ）_
  - _Prompt: Implement the task for spec rapras-yahoo-authentication, first run spec-workflow-guide to get the workflow guide then implement the task: Role: QA Engineer with expertise in pytest-asyncio, mocking Playwright, and testing proxy authentication | Task: Create comprehensive unit tests for YahooAuctionScraper in tests/test_scraper/test_yahoo_scraper.py following Requirements 2 and 4, mocking Playwright to test proxy BASIC auth, phone number input, SMS code prompt, login success/failure, retry logic, and ProxyAuthenticationError | Restrictions: Must mock Playwright and user input, test proxy auth failure (ProxyAuthenticationError, no retry), test SMS input timeout (3 min), verify phone number from .env, test retry logic (max 3 attempts), verify SessionManager.save_session is called, use Given/When/Then comments, achieve 80%+ coverage | Success: Proxy auth tested (success and failure), phone number auto-fill verified, SMS prompt tested with timeout, login success/failure scenarios covered, ProxyAuthenticationError raised on proxy auth failure (no retry), retry logic works for network errors, session cookies saved on success, tests run independently, 80%+ coverage achieved | Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md. After completing implementation, mark as completed ([x]) in tasks.md._

- [x] 10. 統合テスト（E2E）の実装
  - File: tests/integration/test_authentication_flow.py
  - Rapras→Yahoo Auctions認証フローの統合テスト
  - セッション復元テストを含む
  - Purpose: 認証フロー全体の動作を確認
  - _Leverage: pytest、pytest-asyncio、Playwright（実環境）_
  - _Requirements: All（全要件の統合確認）_
  - _Prompt: Implement the task for spec rapras-yahoo-authentication, first run spec-workflow-guide to get the workflow guide then implement the task: Role: QA Automation Engineer with expertise in end-to-end testing and Playwright | Task: Create integration tests in tests/integration/test_authentication_flow.py covering the complete authentication flow: Rapras login → session save → Yahoo Auctions login (proxy + SMS) → session save → next run session restore → skip login, following all requirements | Restrictions: Use real Playwright (not mocked), mark as integration test (pytest.mark.integration), handle real SMS input (may require manual intervention or skip in CI), test session restoration flow, ensure tests can run in isolation, do not commit credentials | Success: Full authentication flow works end-to-end, Rapras login succeeds and saves session, Yahoo Auctions login via proxy succeeds with SMS input, session files are created, next run restores sessions and skips login, integration tests pass locally, clear instructions for manual SMS input | Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md. After completing implementation, mark as completed ([x]) in tasks.md._

- [x] 11. ドキュメント作成とコード品質チェック
  - File: README.md（セットアップ手順追加）、.env.example
  - セットアップ手順、環境変数の説明、使用例を追加
  - Black、Ruff、pytestを実行してコード品質を確認
  - Purpose: ユーザーが認証機能を使用できるようにする
  - _Leverage: Black、Ruff、pytest、pytest-cov_
  - _Requirements: All（全要件のドキュメント化）_
  - _Prompt: Implement the task for spec rapras-yahoo-authentication, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Technical Writer and DevOps Engineer with expertise in Python tooling and documentation | Task: Document authentication setup in README.md, create .env.example with all required variables, and run code quality checks (Black, Ruff, pytest) following all requirements to ensure code quality and usability | Restrictions: Do not include actual credentials in .env.example, ensure setup instructions are clear and complete, run quality checks in order (Black → Ruff → pytest → coverage), verify 80%+ coverage, fix any issues before marking complete | Success: README.md includes clear setup instructions, .env.example contains all required env vars with descriptions, Black formatting applied successfully, Ruff checks pass with no errors, all tests pass, coverage is 80%+, documentation is complete and accurate | Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md. After completing all documentation and quality checks, mark as completed ([x]) in tasks.md._
