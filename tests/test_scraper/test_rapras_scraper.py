"""Unit tests for RaprasScraper class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.scraper.rapras_scraper import LoginError, RaprasScraper
from modules.scraper.session_manager import SessionManager


class TestRaprasScraper:
    """RaprasScraperのテストクラス"""

    @pytest.fixture
    def temp_session_dir(self, tmp_path):
        """一時的なセッションディレクトリを作成"""
        return tmp_path / "test_sessions"

    @pytest.fixture
    def session_manager(self, temp_session_dir):
        """SessionManagerインスタンスを作成"""
        return SessionManager(session_dir=str(temp_session_dir))

    @pytest.fixture
    def rapras_scraper(self, session_manager):
        """RaprasScraperインスタンスを作成"""
        return RaprasScraper(session_manager=session_manager)

    @pytest.fixture
    def mock_playwright(self):
        """Playwrightのモックを作成"""
        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        # async_playwright()の戻り値
        mock_async_pw_instance = AsyncMock()
        mock_async_pw_instance.start.return_value = mock_pw

        # Playwrightの起動チェーン
        mock_pw.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Cookie関連
        mock_context.cookies.return_value = [
            {"name": "session", "value": "test123", "domain": ".rapras.jp"}
        ]

        return {
            "async_pw_instance": mock_async_pw_instance,
            "playwright": mock_pw,
            "browser": mock_browser,
            "context": mock_context,
            "page": mock_page,
        }

    @pytest.mark.asyncio
    async def test_login_success(self, rapras_scraper, mock_playwright):
        """正常系: ログインが成功することを確認"""
        # Given: Playwrightがモックされている
        mock_page = mock_playwright["page"]
        mock_page.query_selector.return_value = MagicMock()  # ログイン状態を示す要素が存在

        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            # When: ログイン
            result = await rapras_scraper.login("test_user", "test_password")

            # Then: ログインに成功
            assert result is True
            mock_page.goto.assert_called()
            mock_page.fill.assert_called()
            mock_page.click.assert_called()

            # Then: セッションが保存される
            assert rapras_scraper.session_manager.session_exists("rapras")

        # クリーンアップ
        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_login_failure_invalid_credentials(self, rapras_scraper, mock_playwright):
        """異常系: 認証情報が誤りの場合にLoginErrorが発生することを確認"""
        # Given: ログイン状態チェックが常にFalseを返す
        mock_page = mock_playwright["page"]
        mock_page.query_selector.return_value = None  # ログイン失敗

        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            # When/Then: LoginErrorが発生
            with pytest.raises(LoginError) as exc_info:
                await rapras_scraper.login("wrong_user", "wrong_password")

            # Then: エラーメッセージが適切
            assert "Login failed after" in str(exc_info.value)

        # クリーンアップ
        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_custom_rapras_url(self, session_manager):
        """正常系: カスタムRapras URLが使用されることを確認"""
        # Given: カスタムURLでRaprasScraperを作成
        custom_url = "https://custom.rapras.jp/"
        scraper = RaprasScraper(session_manager=session_manager, rapras_url=custom_url)

        # Then: カスタムURLが設定される
        assert scraper.rapras_url == custom_url

    @pytest.mark.asyncio
    async def test_max_retries_configuration(self, rapras_scraper):
        """正常系: 最大リトライ回数が正しく設定されることを確認"""
        # Then: デフォルトのリトライ回数が3
        assert rapras_scraper._max_retries == 3
        assert rapras_scraper._retry_delays == [2, 4, 8]

    @pytest.mark.asyncio
    async def test_timeout_configuration(self, rapras_scraper):
        """正常系: タイムアウトが30秒に設定されることを確認"""
        # Then: タイムアウトが30000ms（30秒）
        assert rapras_scraper._timeout == 30000

    @pytest.mark.asyncio
    async def test_login_with_session_restoration(self, rapras_scraper, mock_playwright):
        """正常系: セッション復元が成功した場合のログイン"""
        # Given: 既存のセッションが存在
        mock_page = mock_playwright["page"]
        mock_page.query_selector.return_value = MagicMock()  # ログイン状態

        # セッションを事前に保存
        rapras_scraper.session_manager.save_session(
            "rapras", [{"name": "session", "value": "existing123", "domain": ".rapras.jp"}]
        )

        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            # When: ログイン
            result = await rapras_scraper.login("test_user", "test_password")

            # Then: セッション復元で成功
            assert result is True

        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_login_with_failed_session_restoration(self, rapras_scraper, mock_playwright):
        """正常系: セッション復元が失敗した場合は通常ログイン"""
        # Given: セッションは存在するがログイン状態チェックで失敗→通常ログインで成功
        mock_page = mock_playwright["page"]
        # 最初の呼び出しではNone（セッション復元失敗）、2回目以降True（通常ログイン成功）
        mock_page.query_selector.side_effect = [None, MagicMock(), MagicMock()]

        rapras_scraper.session_manager.save_session(
            "rapras", [{"name": "session", "value": "expired123", "domain": ".rapras.jp"}]
        )

        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            result = await rapras_scraper.login("test_user", "test_password")
            assert result is True

        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_login_timeout_error(self, rapras_scraper, mock_playwright):
        """異常系: タイムアウトが発生した場合"""
        mock_page = mock_playwright["page"]
        # goto()でタイムアウトを発生させる
        mock_page.goto.side_effect = TimeoutError("Navigation timeout")

        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            with pytest.raises(TimeoutError) as exc_info:
                await rapras_scraper.login("test_user", "test_password")

            assert "Login timed out after" in str(exc_info.value)

        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_login_unexpected_error(self, rapras_scraper, mock_playwright):
        """異常系: 予期しないエラーが発生した場合"""
        mock_page = mock_playwright["page"]
        mock_page.goto.side_effect = RuntimeError("Unexpected error")

        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            with pytest.raises(LoginError) as exc_info:
                await rapras_scraper.login("test_user", "test_password")

            assert "Login failed after" in str(exc_info.value)

        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_is_logged_in_without_page(self, rapras_scraper):
        """異常系: ページが存在しない場合はログイン状態チェックがFalse"""
        # Given: ページが初期化されていない
        assert rapras_scraper.page is None

        # When/Then: is_logged_inはFalseを返す
        result = await rapras_scraper.is_logged_in()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_logged_in_with_error(self, rapras_scraper, mock_playwright):
        """異常系: is_logged_in()でエラーが発生した場合"""
        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await rapras_scraper._launch_browser()
            # query_selectorでエラーを発生させる
            rapras_scraper.page.query_selector.side_effect = RuntimeError("Query error")

            result = await rapras_scraper.is_logged_in()
            assert result is False

        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_close_with_error(self, rapras_scraper, mock_playwright):
        """異常系: close()でエラーが発生しても例外を発生させない"""
        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await rapras_scraper._launch_browser()
            # closeでエラーを発生させる
            rapras_scraper.page.close.side_effect = RuntimeError("Close error")

            # エラーを発生させずに正常終了することを確認
            await rapras_scraper.close()
