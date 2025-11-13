"""Unit tests for YahooAuctionScraper class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.scraper.session_manager import SessionManager
from modules.scraper.yahoo_scraper import LoginError, ProxyAuthenticationError, YahooAuctionScraper


@pytest.fixture
def temp_session_dir(tmp_path):
    """一時的なセッションディレクトリを作成"""
    return tmp_path / "test_sessions"


@pytest.fixture
def session_manager(temp_session_dir):
    """SessionManagerインスタンスを作成"""
    return SessionManager(session_dir=str(temp_session_dir))


@pytest.fixture
def proxy_config():
    """プロキシ設定を作成"""
    return {
        "url": "http://164.70.96.2:3128",
        "username": "test_proxy_user",
        "password": "test_proxy_pass",
    }


@pytest.fixture
def yahoo_scraper(session_manager, proxy_config):
    """YahooAuctionScraperインスタンスを作成"""
    return YahooAuctionScraper(session_manager=session_manager, proxy_config=proxy_config)


class TestYahooAuctionScraper:
    """YahooAuctionScraperのテストクラス"""

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

        # get_by_role()のモック（Locatorオブジェクトを返す）
        # get_by_role()は同期関数でLocatorオブジェクトを返す
        mock_locator = MagicMock()
        mock_locator.click = AsyncMock()
        mock_locator.fill = AsyncMock()
        mock_locator.wait_for = AsyncMock(return_value=mock_locator)
        mock_page.get_by_role = MagicMock(return_value=mock_locator)

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
        mock_page.query_selector.return_value = (
            MagicMock()
        )  # ログイン状態（ログアウトボタンが存在）
        mock_page.text_content.return_value = "164.70.96.2"  # プロキシIPアドレス検証用

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
            result = await yahoo_scraper.login(phone_number)

            # Then: ログインに成功
            assert result is True
            # 電話番号入力はget_by_role().fill()、SMSコード入力はpage.fill()を使用
            assert mock_page.fill.call_count >= 1  # SMSコード
            mock_page.get_by_role.assert_called()  # 電話番号入力とボタンクリック

        # クリーンアップ
        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_custom_yahoo_url(self, session_manager, proxy_config):
        """正常系: カスタムYahoo URLが使用されることを確認"""
        # Given: カスタムURLでYahooAuctionScraperを作成
        custom_login_url = "https://custom.yahoo.co.jp/login"
        custom_auctions_url = "https://custom.yahoo.co.jp/auctions"
        scraper = YahooAuctionScraper(
            session_manager=session_manager,
            proxy_config=proxy_config,
            yahoo_login_url=custom_login_url,
            yahoo_auctions_url=custom_auctions_url,
        )

        # Then: カスタムURLが設定される
        assert scraper.yahoo_login_url == custom_login_url
        assert scraper.yahoo_auctions_url == custom_auctions_url

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
        assert yahoo_scraper._retry_delays == [1, 2, 4]

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
        mock_page = mock_playwright["page"]
        mock_page.text_content.return_value = "164.70.96.2"  # 期待されるIPアドレス

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

    @pytest.mark.asyncio
    async def test_verify_proxy_connection_unexpected_error(self, yahoo_scraper, mock_playwright):
        """異常系: プロキシ検証中に予期しないエラーが発生する"""
        # Given: async_playwright().start()で例外が発生
        mock_async_pw = mock_playwright["async_pw_instance"]
        mock_async_pw.start.side_effect = RuntimeError("Unexpected playwright error")

        with patch(
            "modules.scraper.yahoo_scraper.async_playwright",
            return_value=mock_async_pw,
        ):
            # When/Then: ProxyAuthenticationErrorが発生
            with pytest.raises(ProxyAuthenticationError) as exc_info:
                await yahoo_scraper._verify_proxy_connection()

            assert "Proxy verification failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_proxy_connection_cleanup_errors(self, yahoo_scraper, mock_playwright):
        """異常系: プロキシ検証のクリーンアップ中にエラーが発生しても処理を継続"""
        # Given: 各リソースのクローズ時にエラーが発生
        mock_page = mock_playwright["page"]
        mock_context = mock_playwright["context"]
        mock_browser = mock_playwright["browser"]
        mock_pw = mock_playwright["playwright"]

        mock_page.text_content.return_value = "164.70.96.2"  # IPアドレス検証用
        mock_page.close.side_effect = RuntimeError("Page close error")
        mock_context.close.side_effect = RuntimeError("Context close error")
        mock_browser.close.side_effect = RuntimeError("Browser close error")
        mock_pw.stop.side_effect = RuntimeError("Playwright stop error")

        with patch(
            "modules.scraper.yahoo_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            # When: プロキシ検証が実行される（クリーンアップエラーは無視される）
            await yahoo_scraper._verify_proxy_connection()

    @pytest.mark.asyncio
    async def test_restore_session_no_cookies(self, yahoo_scraper, mock_playwright):
        """異常系: セッションにCookieが存在しない場合"""
        # Given: load_sessionがNoneを返す
        with patch.object(yahoo_scraper.session_manager, "load_session", return_value=None):
            # When: セッション復元を試みる
            result = await yahoo_scraper._restore_session()

            # Then: Falseが返される
            assert result is False

    @pytest.mark.asyncio
    async def test_restore_session_exception(self, yahoo_scraper, mock_playwright):
        """異常系: セッション復元中に例外が発生"""
        # Given: ブラウザ起動時に例外が発生
        with (
            patch.object(
                yahoo_scraper.session_manager, "load_session", return_value=[{"name": "test"}]
            ),
            patch.object(
                yahoo_scraper,
                "_launch_browser_with_proxy",
                side_effect=RuntimeError("Browser error"),
            ),
        ):
            # When: セッション復元を試みる
            result = await yahoo_scraper._restore_session()

            # Then: Falseが返される（例外は内部で処理される）
            assert result is False

    @pytest.mark.asyncio
    async def test_prompt_for_sms_code_success(self, yahoo_scraper):
        """正常系: SMS認証コードが正常に入力される"""
        # Given: ユーザーがSMSコードを入力
        expected_code = "123456"

        with patch("asyncio.to_thread", return_value=expected_code):
            # When: SMS認証コード入力を待機
            result = await yahoo_scraper._prompt_for_sms_code()

            # Then: 入力されたコードが返される
            assert result == expected_code

    @pytest.mark.asyncio
    async def test_prompt_for_sms_code_with_whitespace(self, yahoo_scraper):
        """正常系: SMS認証コードに空白が含まれる場合、trimされる"""
        # Given: ユーザーがSMSコードを空白付きで入力
        input_code = "  123456  "
        expected_code = "123456"

        with patch("asyncio.to_thread", return_value=input_code):
            # When: SMS認証コード入力を待機
            result = await yahoo_scraper._prompt_for_sms_code()

            # Then: trimされたコードが返される
            assert result == expected_code

    @pytest.mark.asyncio
    async def test_prompt_for_sms_code_empty_input(self, yahoo_scraper):
        """異常系: 空のSMS認証コードが入力された場合"""
        # Given: ユーザーが空の入力
        with patch("asyncio.to_thread", return_value="   "):
            # When/Then: ValueErrorが発生
            with pytest.raises(ValueError) as exc_info:
                await yahoo_scraper._prompt_for_sms_code()

            assert "SMS code cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_prompt_for_sms_code_timeout(self, yahoo_scraper):
        """異常系: SMS認証コード入力がタイムアウト"""
        # Given: 入力待機がタイムアウト

        async def mock_timeout(*args, **kwargs):
            raise TimeoutError()

        with patch("asyncio.wait_for", side_effect=mock_timeout):
            # When/Then: TimeoutErrorが発生
            with pytest.raises(TimeoutError) as exc_info:
                await yahoo_scraper._prompt_for_sms_code()

            assert "SMS code input timeout" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_is_logged_in_on_login_page(self, yahoo_scraper, mock_playwright):
        """異常系: is_logged_inでlogin.yahoo.co.jpにいる場合はFalse"""
        mock_page = mock_playwright["page"]
        mock_page.url = "https://login.yahoo.co.jp/config/login"

        with patch(
            "modules.scraper.yahoo_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await yahoo_scraper._launch_browser_with_proxy()

            # When: is_logged_inを呼ぶ
            result = await yahoo_scraper.is_logged_in()

            # Then: Falseが返される
            assert result is False

        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_is_logged_in_on_yahoo_without_login_form(self, yahoo_scraper, mock_playwright):
        """正常系: is_logged_inでyahoo.co.jpにいてログインフォームがない場合はTrue"""
        mock_page = mock_playwright["page"]
        mock_page.url = "https://auctions.yahoo.co.jp/"

        # ログアウトリンクもユーザーメニューもない
        async def query_selector_side_effect(selector):
            if "logout" in selector:
                return None
            elif selector == "button[aria-label*='ユーザーメニュー']":
                return None
            elif selector == 'input[name="login"]':
                return None  # ログインフォームがない
            return None

        mock_page.query_selector.side_effect = query_selector_side_effect

        with patch(
            "modules.scraper.yahoo_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await yahoo_scraper._launch_browser_with_proxy()

            # When: is_logged_inを呼ぶ
            result = await yahoo_scraper.is_logged_in()

            # Then: Trueが返される
            assert result is True

        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_extract_seller_name_returns_unknown(self, yahoo_scraper, mock_playwright):
        """異常系: _extract_seller_nameでセラー名が取得できない場合は"不明なセラー"を返す"""
        mock_page = mock_playwright["page"]

        # すべてのセレクタがNoneを返す
        mock_page.query_selector.return_value = None

        with patch(
            "modules.scraper.yahoo_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await yahoo_scraper._launch_browser_with_proxy()

            # When: _extract_seller_nameを呼ぶ
            result = await yahoo_scraper._extract_seller_name()

            # Then: "不明なセラー"が返される
            assert result == "不明なセラー"

        await yahoo_scraper.close()


class TestFetchSellerProducts:
    """fetch_seller_productsメソッドのリトライロジックテスト"""

    def _setup_mock_page_for_fetch(self, yahoo_scraper, seller_name, products):
        """共通のモックページセットアップヘルパー

        Args:
            yahoo_scraper: YahooAuctionScraperインスタンス
            seller_name: モックセラー名
            products: モック商品リスト

        Returns:
            None（yahoo_scraperを直接変更）
        """
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()

        async def mock_extract_seller_name():
            return seller_name

        async def mock_extract_product_titles(max_products):
            return products

        yahoo_scraper.page = mock_page
        yahoo_scraper._launch_browser_with_proxy = AsyncMock()
        yahoo_scraper._extract_seller_name = mock_extract_seller_name
        yahoo_scraper._extract_product_titles = mock_extract_product_titles

    @pytest.mark.asyncio
    async def test_successful_product_fetch_12_items(self, yahoo_scraper):
        """正常系: 12件の商品を正常に取得できることを確認

        Given: 12件の商品を持つYahoo Auctionsセラーページ
        When: fetch_seller_productsを呼び出す
        Then: seller_name、seller_url、12件のproduct_titlesを含むdictが返される
        """
        # Given
        seller_url = "https://auctions.yahoo.co.jp/seller/test_seller"
        expected_products = [f"Product {i}" for i in range(1, 13)]
        self._setup_mock_page_for_fetch(yahoo_scraper, "Test Seller", expected_products)

        # When
        result = await yahoo_scraper.fetch_seller_products(seller_url, max_products=12)

        # Then
        assert result["seller_name"] == "Test Seller"
        assert result["seller_url"] == seller_url
        assert len(result["product_titles"]) == 12
        assert result["product_titles"] == expected_products

    @pytest.mark.asyncio
    async def test_fetch_with_less_than_12_products(self, yahoo_scraper, caplog):
        """正常系: 12件未満の商品で警告ログが出力されることを確認

        Given: 8件の商品を持つYahoo Auctionsセラーページ
        When: fetch_seller_productsをmax_products=12で呼び出す
        Then: 8件の商品を返し、警告をログ出力する
        """
        # Given
        seller_url = "https://auctions.yahoo.co.jp/seller/test_seller"
        expected_products = [f"Product {i}" for i in range(1, 9)]
        self._setup_mock_page_for_fetch(yahoo_scraper, "Test Seller", expected_products)

        # When
        result = await yahoo_scraper.fetch_seller_products(seller_url, max_products=12)

        # Then
        assert len(result["product_titles"]) == 8
        assert "商品数が12件未満です（8件）" in caplog.text

    @pytest.mark.asyncio
    async def test_fetch_with_zero_products(self, yahoo_scraper, caplog):
        """正常系: 商品が0件の場合の動作を確認

        Given: 商品が0件のYahoo Auctionsセラーページ
        When: fetch_seller_productsを呼び出す
        Then: 空のproduct_titlesリストを返し、警告をログ出力する
        """
        # Given
        seller_url = "https://auctions.yahoo.co.jp/seller/test_seller"
        self._setup_mock_page_for_fetch(yahoo_scraper, "Test Seller", [])

        # When
        result = await yahoo_scraper.fetch_seller_products(seller_url, max_products=12)

        # Then
        assert len(result["product_titles"]) == 0
        assert "商品数が12件未満です（0件）" in caplog.text

    @pytest.mark.asyncio
    async def test_retry_logic_fail_twice_succeed_third(self, yahoo_scraper, mocker):
        """正常系: 2回失敗後、3回目のリトライで成功することを確認

        Given: Yahoo Auctions接続が2回失敗後に成功
        When: fetch_seller_productsを呼び出す
        Then: exponential backoff（1s, 2s）で2回リトライし、3回目で結果を返す
        """
        # Given
        seller_url = "https://auctions.yahoo.co.jp/seller/test_seller"
        expected_products = [f"Product {i}" for i in range(1, 13)]

        # Mock browser interactions
        mock_page = AsyncMock()
        # Fail twice, then succeed
        call_count = {"count": 0}

        async def mock_goto(url, timeout):
            call_count["count"] += 1
            if call_count["count"] <= 2:
                raise TimeoutError("Connection timeout")
            # Success on 3rd attempt
            return None

        mock_page.goto = mock_goto

        # Mock _extract_seller_name
        async def mock_extract_seller_name():
            return "Test Seller"

        # Mock _extract_product_titles
        async def mock_extract_product_titles(max_products):
            return expected_products

        yahoo_scraper.page = mock_page
        yahoo_scraper._launch_browser_with_proxy = AsyncMock()
        yahoo_scraper._extract_seller_name = mock_extract_seller_name
        yahoo_scraper._extract_product_titles = mock_extract_product_titles

        # Mock sleep to verify backoff timing
        mock_sleep = mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        # When
        result = await yahoo_scraper.fetch_seller_products(seller_url, max_products=12)

        # Then
        assert result["seller_name"] == "Test Seller"
        assert len(result["product_titles"]) == 12
        # Verify exponential backoff (1s, 2s)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)

    @pytest.mark.asyncio
    async def test_connection_error_after_3_retries(self, yahoo_scraper, mocker):
        """異常系: 3回のリトライ失敗後にConnectionErrorが発生することを確認

        Given: Yahoo Auctions接続が3回失敗
        When: fetch_seller_productsを呼び出す
        Then: 3回のリトライ後にConnectionErrorが発生
        """
        # Given
        seller_url = "https://auctions.yahoo.co.jp/seller/test_seller"

        # Mock browser interactions to always fail
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(side_effect=TimeoutError("Connection timeout"))

        yahoo_scraper.page = mock_page
        yahoo_scraper._launch_browser_with_proxy = AsyncMock()

        # Mock sleep to speed up test
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        # When/Then
        with pytest.raises(
            ConnectionError, match="Yahoo Auctionsへの接続が3回のリトライ後も失敗しました"
        ):
            await yahoo_scraper.fetch_seller_products(seller_url, max_products=12)

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self, yahoo_scraper, mocker):
        """正常系: exponential backoffのタイミング（1s, 2s, 4s）が正しいことを確認

        Given: Yahoo Auctions接続が3回失敗
        When: fetch_seller_productsを呼び出す
        Then: 最初の2回のリトライでbackoffタイミングが1s, 2sであることを検証
        """
        # Given
        seller_url = "https://auctions.yahoo.co.jp/seller/test_seller"

        # Mock browser interactions to always fail
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock(side_effect=TimeoutError("Connection timeout"))

        yahoo_scraper.page = mock_page
        yahoo_scraper._launch_browser_with_proxy = AsyncMock()

        # Mock sleep to verify backoff timing
        mock_sleep = mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        # When/Then
        with pytest.raises(ConnectionError):
            await yahoo_scraper.fetch_seller_products(seller_url, max_products=12)

        # Then: Verify exponential backoff (1s, 2s)
        assert mock_sleep.call_count == 2
        calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert calls == [1, 2]

    @pytest.mark.asyncio
    async def test_proxy_configuration_applied(self, yahoo_scraper, mocker):
        """正常系: プロキシ設定が正しく適用されることを確認

        Given: プロキシ設定を持つYahooAuctionScraper
        When: ブラウザが起動される
        Then: プロキシ設定がブラウザコンテキストに適用される
        """
        # Given
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)

        # Mock async_playwright context manager
        mocker.patch(
            "modules.scraper.yahoo_scraper.async_playwright",
            return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_playwright)),
        )

        yahoo_scraper.playwright = mock_playwright
        yahoo_scraper.browser = mock_browser

        # When
        await yahoo_scraper._launch_browser_with_proxy()

        # Then
        mock_browser.new_context.assert_called_once()
        call_kwargs = mock_browser.new_context.call_args.kwargs
        assert "proxy" in call_kwargs
        assert call_kwargs["proxy"]["server"] == "http://164.70.96.2:3128"
        assert call_kwargs["proxy"]["username"] == "test_proxy_user"
        assert call_kwargs["proxy"]["password"] == "test_proxy_pass"


class TestRetryBackoffConstants:
    """modules.config.constantsのリトライバックオフ定数のテスト"""

    def test_retry_backoff_seconds_constant(self):
        """正常系: RETRY_BACKOFF_SECONDS定数が正しく定義されることを確認

        Given: modules.config.constantsのRETRY_BACKOFF_SECONDS定数
        When: 定数をインポートする
        Then: exponential backoff値（1, 2, 4）を含む
        """
        # Given/When
        from modules.config.constants import RETRY_BACKOFF_SECONDS

        # Then
        assert RETRY_BACKOFF_SECONDS == (1, 2, 4)
        assert len(RETRY_BACKOFF_SECONDS) == 3
