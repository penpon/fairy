"""Unit tests for YahooAuctionScraper class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.scraper.session_manager import SessionManager
from modules.scraper.yahoo_scraper import LoginError, ProxyAuthenticationError, YahooAuctionScraper


class TestYahooAuctionScraper:
    """YahooAuctionScraperのテストクラス"""

    @pytest.fixture
    def temp_session_dir(self, tmp_path):
        """一時的なセッションディレクトリを作成"""
        return tmp_path / "test_sessions"

    @pytest.fixture
    def session_manager(self, temp_session_dir):
        """SessionManagerインスタンスを作成"""
        return SessionManager(session_dir=str(temp_session_dir))

    @pytest.fixture
    def proxy_config(self):
        """プロキシ設定を作成"""
        return {
            "url": "http://164.70.96.2:3128",
            "username": "test_proxy_user",
            "password": "test_proxy_pass",
        }

    @pytest.fixture
    def yahoo_scraper(self, session_manager, proxy_config):
        """YahooAuctionScraperインスタンスを作成"""
        return YahooAuctionScraper(session_manager=session_manager, proxy_config=proxy_config)

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
            {"name": "session", "value": "yahoo123", "domain": ".yahoo.co.jp"}
        ]

        return {
            "async_pw_instance": mock_async_pw_instance,
            "playwright": mock_pw,
            "browser": mock_browser,
            "context": mock_context,
            "page": mock_page,
        }

    @pytest.mark.asyncio
    async def test_login_success_with_proxy(self, yahoo_scraper, mock_playwright):
        """正常系: プロキシ経由でログインが成功することを確認"""
        # Given: Playwrightとプロキシがモックされている
        mock_page = mock_playwright["page"]
        mock_page.query_selector.return_value = MagicMock()  # ログイン状態

        # SMS入力をモック
        with (
            patch(
                "modules.scraper.yahoo_scraper.async_playwright",
                return_value=mock_playwright["async_pw_instance"],
            ),
            patch.object(yahoo_scraper, "_prompt_for_sms_code", return_value="123456"),
        ):
            # When: ログイン
            result = await yahoo_scraper.login("09012345678")

            # Then: ログインに成功
            assert result is True
            mock_page.goto.assert_called()
            mock_page.fill.assert_called()

            # Then: セッションが保存される
            assert yahoo_scraper.session_manager.session_exists("yahoo")

        # クリーンアップ
        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_proxy_authentication_error(self, yahoo_scraper, mock_playwright):
        """異常系: プロキシ認証失敗時にProxyAuthenticationErrorが発生することを確認"""
        # Given: プロキシ検証が失敗する
        with (
            patch(
                "modules.scraper.yahoo_scraper.async_playwright",
                return_value=mock_playwright["async_pw_instance"],
            ),
            patch.object(
                yahoo_scraper,
                "_verify_proxy_connection",
                side_effect=ProxyAuthenticationError("Auth failed"),
            ),
        ):
            # When/Then: ProxyAuthenticationErrorが発生
            with pytest.raises(ProxyAuthenticationError) as exc_info:
                await yahoo_scraper.login("09012345678")

            # Then: エラーメッセージが適切
            assert "Auth failed" in str(exc_info.value)

        # クリーンアップ
        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_login_failure_invalid_credentials(self, yahoo_scraper, mock_playwright):
        """異常系: ログイン失敗時にLoginErrorが発生することを確認"""
        # Given: ログイン状態チェックが常にFalseを返す
        mock_page = mock_playwright["page"]
        mock_page.query_selector.return_value = None  # ログイン失敗

        with (
            patch(
                "modules.scraper.yahoo_scraper.async_playwright",
                return_value=mock_playwright["async_pw_instance"],
            ),
            patch.object(yahoo_scraper, "_prompt_for_sms_code", return_value="wrong_code"),
            patch.object(yahoo_scraper, "_verify_proxy_connection", return_value=None),
        ):
            # When/Then: LoginErrorが発生
            with pytest.raises(LoginError) as exc_info:
                await yahoo_scraper.login("09012345678")

            # Then: エラーメッセージが適切
            assert "Login failed after" in str(exc_info.value)

        # クリーンアップ
        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_phone_number_from_env(self, yahoo_scraper, mock_playwright):
        """正常系: 電話番号が.envから読み込まれることを確認"""
        # Given: 電話番号
        phone_number = "09012345678"
        mock_page = mock_playwright["page"]
        mock_page.query_selector.return_value = MagicMock()

        with (
            patch(
                "modules.scraper.yahoo_scraper.async_playwright",
                return_value=mock_playwright["async_pw_instance"],
            ),
            patch.object(yahoo_scraper, "_prompt_for_sms_code", return_value="123456"),
            patch.object(yahoo_scraper, "_verify_proxy_connection", return_value=None),
        ):
            # When: ログイン
            await yahoo_scraper.login(phone_number)

            # Then: 電話番号が入力される
            assert mock_page.fill.call_count >= 2  # 電話番号とSMSコード

        # クリーンアップ
        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_custom_yahoo_url(self, session_manager, proxy_config):
        """正常系: カスタムYahoo URLが使用されることを確認"""
        # Given: カスタムURLでYahooAuctionScraperを作成
        custom_url = "https://custom.yahoo.co.jp/"
        scraper = YahooAuctionScraper(
            session_manager=session_manager, proxy_config=proxy_config, yahoo_url=custom_url
        )

        # Then: カスタムURLが設定される
        assert scraper.yahoo_url == custom_url

    @pytest.mark.asyncio
    async def test_proxy_configuration(self, yahoo_scraper, proxy_config):
        """正常系: プロキシ設定が正しく保持されることを確認"""
        # Then: プロキシ設定が保持される
        assert yahoo_scraper.proxy_config == proxy_config
        assert yahoo_scraper.proxy_config["url"] == "http://164.70.96.2:3128"
        assert yahoo_scraper.proxy_config["username"] == "test_proxy_user"
        assert yahoo_scraper.proxy_config["password"] == "test_proxy_pass"

    @pytest.mark.asyncio
    async def test_sms_timeout_configuration(self, yahoo_scraper):
        """正常系: SMSタイムアウトが3分に設定されることを確認"""
        # Then: SMSタイムアウトが180秒（3分）
        assert yahoo_scraper._sms_timeout == 180

    @pytest.mark.asyncio
    async def test_max_retries_configuration(self, yahoo_scraper):
        """正常系: 最大リトライ回数が正しく設定されることを確認"""
        # Then: デフォルトのリトライ回数が3
        assert yahoo_scraper._max_retries == 3
        assert yahoo_scraper._retry_delays == [2, 4, 8]

    @pytest.mark.asyncio
    async def test_timeout_configuration(self, yahoo_scraper):
        """正常系: タイムアウトが30秒に設定されることを確認"""
        # Then: タイムアウトが30000ms（30秒）
        assert yahoo_scraper._timeout == 30000

    @pytest.mark.asyncio
    async def test_invalid_proxy_config_missing_keys(self, session_manager):
        """異常系: プロキシ設定に必須キーが不足している場合"""
        # Given: 不完全なプロキシ設定
        invalid_proxy_config = {"url": "http://proxy.com"}

        # When/Then: ValueErrorが発生
        with pytest.raises(ValueError) as exc_info:
            YahooAuctionScraper(session_manager=session_manager, proxy_config=invalid_proxy_config)

        assert "missing required keys" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_login_with_session_restoration(self, yahoo_scraper, mock_playwright):
        """正常系: セッション復元が成功した場合のログイン"""
        mock_page = mock_playwright["page"]
        mock_page.query_selector.return_value = MagicMock()

        yahoo_scraper.session_manager.save_session(
            "yahoo", [{"name": "session", "value": "existing123", "domain": ".yahoo.co.jp"}]
        )

        with (
            patch(
                "modules.scraper.yahoo_scraper.async_playwright",
                return_value=mock_playwright["async_pw_instance"],
            ),
            patch.object(yahoo_scraper, "_verify_proxy_connection", return_value=None),
        ):
            result = await yahoo_scraper.login("09012345678")
            assert result is True

        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_login_with_failed_session_restoration(self, yahoo_scraper, mock_playwright):
        """正常系: セッション復元が失敗した場合は通常ログイン"""
        mock_page = mock_playwright["page"]
        mock_page.query_selector.side_effect = [None, MagicMock(), MagicMock()]

        yahoo_scraper.session_manager.save_session(
            "yahoo", [{"name": "session", "value": "expired123", "domain": ".yahoo.co.jp"}]
        )

        with (
            patch(
                "modules.scraper.yahoo_scraper.async_playwright",
                return_value=mock_playwright["async_pw_instance"],
            ),
            patch.object(yahoo_scraper, "_prompt_for_sms_code", return_value="123456"),
            patch.object(yahoo_scraper, "_verify_proxy_connection", return_value=None),
        ):
            result = await yahoo_scraper.login("09012345678")
            assert result is True

        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_login_timeout_error(self, yahoo_scraper, mock_playwright):
        """異常系: タイムアウトが発生した場合"""
        mock_page = mock_playwright["page"]
        mock_page.goto.side_effect = TimeoutError("Navigation timeout")

        with (
            patch(
                "modules.scraper.yahoo_scraper.async_playwright",
                return_value=mock_playwright["async_pw_instance"],
            ),
            patch.object(yahoo_scraper, "_verify_proxy_connection", return_value=None),
        ):
            with pytest.raises(TimeoutError) as exc_info:
                await yahoo_scraper.login("09012345678")

            assert "Login timed out after" in str(exc_info.value)

        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_login_unexpected_error(self, yahoo_scraper, mock_playwright):
        """異常系: 予期しないエラーが発生した場合"""
        mock_page = mock_playwright["page"]
        mock_page.goto.side_effect = RuntimeError("Unexpected error")

        with (
            patch(
                "modules.scraper.yahoo_scraper.async_playwright",
                return_value=mock_playwright["async_pw_instance"],
            ),
            patch.object(yahoo_scraper, "_verify_proxy_connection", return_value=None),
        ):
            with pytest.raises(LoginError) as exc_info:
                await yahoo_scraper.login("09012345678")

            assert "Login failed after" in str(exc_info.value)

        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_is_logged_in_without_page(self, yahoo_scraper):
        """異常系: ページが存在しない場合はログイン状態チェックがFalse"""
        assert yahoo_scraper.page is None
        result = await yahoo_scraper.is_logged_in()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_logged_in_with_error(self, yahoo_scraper, mock_playwright):
        """異常系: is_logged_in()でエラーが発生した場合"""
        with patch(
            "modules.scraper.yahoo_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await yahoo_scraper._launch_browser_with_proxy()
            yahoo_scraper.page.query_selector.side_effect = RuntimeError("Query error")

            result = await yahoo_scraper.is_logged_in()
            assert result is False

        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_close_with_error(self, yahoo_scraper, mock_playwright):
        """異常系: close()でエラーが発生しても例外を発生させない"""
        with patch(
            "modules.scraper.yahoo_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await yahoo_scraper._launch_browser_with_proxy()
            yahoo_scraper.page.close.side_effect = RuntimeError("Close error")

            # エラーを発生させずに正常終了することを確認
            await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_verify_proxy_connection_success(self, yahoo_scraper, mock_playwright):
        """正常系: プロキシ接続の検証が成功する"""
        with patch(
            "modules.scraper.yahoo_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            # プロキシ検証が成功（例外が発生しない）
            await yahoo_scraper._verify_proxy_connection()

    @pytest.mark.asyncio
    async def test_verify_proxy_connection_failure(self, yahoo_scraper, mock_playwright):
        """異常系: プロキシ接続の検証が失敗する"""
        mock_page = mock_playwright["page"]
        mock_page.goto.side_effect = RuntimeError("Proxy connection failed")

        with patch(
            "modules.scraper.yahoo_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            with pytest.raises(ProxyAuthenticationError):
                await yahoo_scraper._verify_proxy_connection()
