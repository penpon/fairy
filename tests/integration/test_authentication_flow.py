"""Integration tests for Rapras authentication flow.

This test module covers the end-to-end Rapras authentication flow:
1. Rapras login → session save
2. Next run: session restore → skip login

IMPORTANT: These tests require real credentials in .env file.
Run with: pytest -m integration
Skip with: pytest -m "not integration"

Setup requirements:
- .env file with valid credentials (RAPRAS_USERNAME, RAPRAS_PASSWORD)
- Playwright browsers installed: playwright install chromium

Security notes:
- DO NOT commit credentials
- Tests use real Playwright (not mocked)
- Session files are created in tests/integration/test_sessions/
- Clean up session files after tests
"""

import shutil

import pytest

from modules.config.settings import load_rapras_config
from modules.scraper.rapras_scraper import RaprasScraper
from modules.scraper.session_manager import SessionManager


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
