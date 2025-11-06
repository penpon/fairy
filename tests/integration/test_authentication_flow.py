"""Integration tests for complete authentication flow.

This test module covers the end-to-end authentication flow:
1. Rapras login → session save
2. Yahoo Auctions login (proxy + SMS) → session save
3. Next run: session restore → skip login

IMPORTANT: These tests require real credentials in .env file and may require manual SMS input.
Run with: pytest -m integration
Skip with: pytest -m "not integration"

Setup requirements:
- .env file with valid credentials (RAPRAS_USERNAME, RAPRAS_PASSWORD, YAHOO_PHONE_NUMBER, etc.)
- Playwright browsers installed: playwright install chromium
- Manual SMS code input during Yahoo Auctions login test

Security notes:
- DO NOT commit credentials
- Tests use real Playwright (not mocked)
- Session files are created in tests/integration/test_sessions/
- Clean up session files after tests
"""

import shutil

import pytest

from modules.config.settings import load_proxy_config, load_rapras_config, load_yahoo_config
from modules.scraper.rapras_scraper import RaprasScraper
from modules.scraper.session_manager import SessionManager
from modules.scraper.yahoo_scraper import YahooAuctionScraper


@pytest.fixture
def integration_session_dir(tmp_path):
    """統合テスト用の一時セッションディレクトリを作成"""
    session_dir = tmp_path / "test_sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    yield session_dir

    # クリーンアップ: テスト後にセッションファイルを削除
    if session_dir.exists():
        shutil.rmtree(session_dir)


@pytest.fixture
def session_manager(integration_session_dir):
    """統合テスト用のSessionManagerインスタンスを作成"""
    return SessionManager(session_dir=str(integration_session_dir))


@pytest.mark.integration
class TestRaprasAuthenticationFlow:
    """Rapras認証フローの統合テスト"""

    @pytest.mark.asyncio
    async def test_rapras_login_and_session_save(self, session_manager):
        """
        統合テスト: Raprasログイン → セッション保存

        Given: .envファイルにRapras認証情報が設定されている
        When: RaprasScraper.login()を実行
        Then: ログインに成功し、セッションCookieが保存される
        """
        # Given: Rapras認証情報をロード
        try:
            rapras_config = load_rapras_config()
        except Exception as e:
            pytest.skip(f"Rapras config not available: {e}")

        rapras_scraper = RaprasScraper(session_manager=session_manager)

        try:
            # When: Raprasにログイン
            login_result = await rapras_scraper.login(
                rapras_config.username, rapras_config.password
            )

            # Then: ログインに成功
            assert login_result is True, "Rapras login should succeed"

            # Then: ログイン状態を確認
            is_logged_in = await rapras_scraper.is_logged_in()
            assert is_logged_in is True, "Should be logged in after successful login"

            # Then: セッションファイルが作成される
            assert session_manager.session_exists("rapras"), "Rapras session file should be created"

        finally:
            # クリーンアップ
            await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_rapras_session_restoration(self, session_manager):
        """
        統合テスト: Raprasセッション復元 → ログインスキップ

        Given: Raprasセッションファイルが存在する
        When: RaprasScraper.login()を実行（セッション復元）
        Then: ログイン処理をスキップし、既存セッションを使用する
        """
        # Given: Rapras認証情報をロード
        try:
            rapras_config = load_rapras_config()
        except Exception as e:
            pytest.skip(f"Rapras config not available: {e}")

        # Given: 最初にログインしてセッションを作成
        rapras_scraper_initial = RaprasScraper(session_manager=session_manager)

        try:
            # 初回ログイン
            await rapras_scraper_initial.login(rapras_config.username, rapras_config.password)
            assert session_manager.session_exists("rapras"), "Session should be created"

        finally:
            await rapras_scraper_initial.close()

        # When: 新しいScraperインスタンスでセッション復元
        rapras_scraper_restored = RaprasScraper(session_manager=session_manager)

        try:
            # セッションを復元してログイン
            login_result = await rapras_scraper_restored.login(
                rapras_config.username, rapras_config.password
            )

            # Then: ログインに成功（セッション復元）
            assert login_result is True, "Login with restored session should succeed"

            # Then: ログイン状態を確認
            is_logged_in = await rapras_scraper_restored.is_logged_in()
            assert is_logged_in is True, "Should be logged in after session restoration"

        finally:
            # クリーンアップ
            await rapras_scraper_restored.close()


@pytest.mark.integration
class TestYahooAuctionsAuthenticationFlow:
    """Yahoo Auctions認証フローの統合テスト"""

    @pytest.mark.asyncio
    async def test_yahoo_login_with_proxy_and_sms(self, session_manager):
        """
        統合テスト: Yahoo Auctionsログイン（プロキシ + SMS） → セッション保存

        Given: .envファイルにYahoo認証情報とプロキシ設定がある
        When: YahooAuctionScraper.login()を実行
        Then: プロキシ経由で接続し、SMS入力後にログインに成功し、セッションが保存される

        NOTE: このテストは手動SMS入力が必要です（タイムアウト: 3分）
        """
        # Given: Yahoo認証情報とプロキシ設定をロード
        try:
            yahoo_config = load_yahoo_config()
            proxy_config_obj = load_proxy_config()
        except Exception as e:
            pytest.skip(f"Yahoo/Proxy config not available: {e}")

        # プロキシ設定を辞書形式に変換
        proxy_config = {
            "url": proxy_config_obj.url,
            "username": proxy_config_obj.username,
            "password": proxy_config_obj.password,
        }

        yahoo_scraper = YahooAuctionScraper(
            session_manager=session_manager, proxy_config=proxy_config
        )

        try:
            print("\n" + "=" * 70)
            print("Yahoo Auctions統合テスト")
            print("SMS認証コードの入力が必要です（タイムアウト: 3分）")
            print("スマートフォンでSMSを受信後、コードを入力してください")
            print("=" * 70)

            # When: Yahoo Auctionsにログイン（SMS入力が必要）
            login_result = await yahoo_scraper.login(yahoo_config.phone_number)

            # Then: ログインに成功
            assert login_result is True, "Yahoo Auctions login should succeed"

            # Then: ログイン状態を確認
            is_logged_in = await yahoo_scraper.is_logged_in()
            assert is_logged_in is True, "Should be logged in after successful login"

            # Then: セッションファイルが作成される
            assert session_manager.session_exists("yahoo"), "Yahoo session file should be created"

        finally:
            # クリーンアップ
            await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_yahoo_session_restoration(self, session_manager):
        """
        統合テスト: Yahoo Auctionsセッション復元 → ログインスキップ

        Given: Yahoo Auctionsセッションファイルが存在する
        When: YahooAuctionScraper.login()を実行（セッション復元）
        Then: ログイン処理（SMS入力）をスキップし、既存セッションを使用する
        """
        # Given: Yahoo認証情報とプロキシ設定をロード
        try:
            yahoo_config = load_yahoo_config()
            proxy_config_obj = load_proxy_config()
        except Exception as e:
            pytest.skip(f"Yahoo/Proxy config not available: {e}")

        # プロキシ設定を辞書形式に変換
        proxy_config = {
            "url": proxy_config_obj.url,
            "username": proxy_config_obj.username,
            "password": proxy_config_obj.password,
        }

        # Given: 既存のセッションファイルがあることを確認
        if not session_manager.session_exists("yahoo"):
            pytest.skip(
                "Yahoo session file not found. Run test_yahoo_login_with_proxy_and_sms first."
            )

        # When: 新しいScraperインスタンスでセッション復元
        yahoo_scraper_restored = YahooAuctionScraper(
            session_manager=session_manager, proxy_config=proxy_config
        )

        try:
            print("\n" + "=" * 70)
            print("Yahoo Auctionsセッション復元テスト")
            print("既存セッションを使用するため、SMS入力は不要です")
            print("=" * 70)

            # セッションを復元してログイン
            login_result = await yahoo_scraper_restored.login(yahoo_config.phone_number)

            # Then: ログインに成功（セッション復元）
            assert login_result is True, "Login with restored session should succeed"

            # Then: ログイン状態を確認
            is_logged_in = await yahoo_scraper_restored.is_logged_in()
            assert is_logged_in is True, "Should be logged in after session restoration"

        finally:
            # クリーンアップ
            await yahoo_scraper_restored.close()


@pytest.mark.integration
class TestCompleteAuthenticationFlow:
    """完全な認証フローの統合テスト（Rapras → Yahoo Auctions）"""

    @pytest.mark.asyncio
    async def test_complete_authentication_flow(self, session_manager):
        """
        統合テスト: 完全な認証フロー

        Given: .envファイルに全ての認証情報が設定されている
        When: Raprasログイン → Yahoo Auctionsログイン
        Then: 両方のログインに成功し、セッションが保存される

        NOTE: このテストは手動SMS入力が必要です
        """
        # Given: 全ての認証情報をロード
        try:
            rapras_config = load_rapras_config()
            yahoo_config = load_yahoo_config()
            proxy_config_obj = load_proxy_config()
        except Exception as e:
            pytest.skip(f"Config not available: {e}")

        # プロキシ設定を辞書形式に変換
        proxy_config = {
            "url": proxy_config_obj.url,
            "username": proxy_config_obj.username,
            "password": proxy_config_obj.password,
        }

        print("\n" + "=" * 70)
        print("完全な認証フローテスト")
        print("1. Raprasログイン")
        print("2. Yahoo Auctionsログイン（SMS入力が必要）")
        print("=" * 70)

        # ステップ1: Raprasログイン
        rapras_scraper = RaprasScraper(session_manager=session_manager)

        try:
            print("\n[1/2] Raprasにログイン中...")
            rapras_login_result = await rapras_scraper.login(
                rapras_config.username, rapras_config.password
            )

            # Then: Raprasログインに成功
            assert rapras_login_result is True, "Rapras login should succeed"
            assert session_manager.session_exists("rapras"), "Rapras session should be saved"
            print("✓ Raprasログイン成功")

        finally:
            await rapras_scraper.close()

        # ステップ2: Yahoo Auctionsログイン
        yahoo_scraper = YahooAuctionScraper(
            session_manager=session_manager, proxy_config=proxy_config
        )

        try:
            print("\n[2/2] Yahoo Auctionsにログイン中（SMS入力が必要）...")
            yahoo_login_result = await yahoo_scraper.login(yahoo_config.phone_number)

            # Then: Yahoo Auctionsログインに成功
            assert yahoo_login_result is True, "Yahoo Auctions login should succeed"
            assert session_manager.session_exists("yahoo"), "Yahoo session should be saved"
            print("✓ Yahoo Auctionsログイン成功")

        finally:
            await yahoo_scraper.close()

        # Then: 両方のセッションファイルが存在
        assert session_manager.session_exists("rapras"), "Rapras session should exist"
        assert session_manager.session_exists("yahoo"), "Yahoo session should exist"

        print("\n" + "=" * 70)
        print("✓ 完全な認証フロー成功")
        print("=" * 70)

    @pytest.mark.asyncio
    async def test_complete_session_restoration_flow(self, session_manager):
        """
        統合テスト: 完全なセッション復元フロー

        Given: RaprasとYahoo Auctionsのセッションファイルが存在する
        When: 両方のScraperでセッション復元を実行
        Then: ログイン処理をスキップし、既存セッションを使用する

        NOTE: このテストは既存のセッションファイルが必要です
        test_complete_authentication_flowを先に実行してください
        """
        # Given: 全ての認証情報をロード
        try:
            rapras_config = load_rapras_config()
            yahoo_config = load_yahoo_config()
            proxy_config_obj = load_proxy_config()
        except Exception as e:
            pytest.skip(f"Config not available: {e}")

        # Given: セッションファイルの存在を確認
        if not session_manager.session_exists("rapras") or not session_manager.session_exists(
            "yahoo"
        ):
            pytest.skip("Session files not found. Run test_complete_authentication_flow first.")

        # プロキシ設定を辞書形式に変換
        proxy_config = {
            "url": proxy_config_obj.url,
            "username": proxy_config_obj.username,
            "password": proxy_config_obj.password,
        }

        print("\n" + "=" * 70)
        print("完全なセッション復元フローテスト")
        print("既存セッションを使用するため、認証情報入力・SMS入力は不要です")
        print("=" * 70)

        # ステップ1: Raprasセッション復元
        rapras_scraper = RaprasScraper(session_manager=session_manager)

        try:
            print("\n[1/2] Raprasセッションを復元中...")
            rapras_login_result = await rapras_scraper.login(
                rapras_config.username, rapras_config.password
            )

            # Then: セッション復元に成功
            assert rapras_login_result is True, "Rapras session restoration should succeed"
            is_logged_in = await rapras_scraper.is_logged_in()
            assert is_logged_in is True, "Should be logged in via restored session"
            print("✓ Raprasセッション復元成功")

        finally:
            await rapras_scraper.close()

        # ステップ2: Yahoo Auctionsセッション復元
        yahoo_scraper = YahooAuctionScraper(
            session_manager=session_manager, proxy_config=proxy_config
        )

        try:
            print("\n[2/2] Yahoo Auctionsセッションを復元中...")
            yahoo_login_result = await yahoo_scraper.login(yahoo_config.phone_number)

            # Then: セッション復元に成功
            assert yahoo_login_result is True, "Yahoo Auctions session restoration should succeed"
            is_logged_in = await yahoo_scraper.is_logged_in()
            assert is_logged_in is True, "Should be logged in via restored session"
            print("✓ Yahoo Auctionsセッション復元成功")

        finally:
            await yahoo_scraper.close()

        print("\n" + "=" * 70)
        print("✓ 完全なセッション復元フロー成功")
        print("=" * 70)
