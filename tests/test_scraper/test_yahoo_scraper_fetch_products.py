"""Unit tests for YahooAuctionScraper.fetch_seller_products method."""

from unittest.mock import AsyncMock, patch

import pytest

from modules.scraper.session_manager import SessionManager
from modules.scraper.yahoo_scraper import YahooAuctionScraper


class TestFetchSellerProducts:
    """YahooAuctionScraper.fetch_seller_productsのテストクラス"""

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

        return {
            "async_pw_instance": mock_async_pw_instance,
            "playwright": mock_pw,
            "browser": mock_browser,
            "context": mock_context,
            "page": mock_page,
        }

    @pytest.mark.asyncio
    async def test_fetch_seller_products_success_12_items(self, yahoo_scraper, mock_playwright):
        """正常系: 12件の商品を取得成功"""
        # Given: モックされたPlaywrightとセラーページ
        seller_url = "https://auctions.yahoo.co.jp/sellinglist/test_seller?user_type=c"
        mock_page = mock_playwright["page"]

        # セラー名のモック
        mock_seller_name_element = AsyncMock()
        mock_seller_name_element.text_content.return_value = "テストセラー"
        mock_page.query_selector.return_value = mock_seller_name_element

        # 12件の商品をモック
        mock_product_elements = []
        for i in range(12):
            mock_element = AsyncMock()
            mock_element.text_content.return_value = f"商品タイトル {i + 1}"
            mock_product_elements.append(mock_element)

        mock_page.query_selector_all.return_value = mock_product_elements

        with patch(
            "modules.scraper.yahoo_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            # When: fetch_seller_productsを呼び出し
            result = await yahoo_scraper.fetch_seller_products(seller_url)

            # Then: 12件の商品情報が返される
            assert result["seller_name"] == "テストセラー"
            assert result["seller_url"] == seller_url
            assert len(result["product_titles"]) == 12
            assert result["product_titles"][0] == "商品タイトル 1"
            assert result["product_titles"][11] == "商品タイトル 12"

        # クリーンアップ
        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_products_less_than_12_items(self, yahoo_scraper, mock_playwright):
        """正常系: 12件未満の商品を取得し、警告ログが記録される"""
        # Given: モックされたPlaywrightと8件の商品
        seller_url = "https://auctions.yahoo.co.jp/sellinglist/test_seller"
        mock_page = mock_playwright["page"]

        mock_seller_name_element = AsyncMock()
        mock_seller_name_element.text_content.return_value = "少数商品セラー"
        mock_page.query_selector.return_value = mock_seller_name_element

        # 8件の商品をモック
        mock_product_elements = []
        for i in range(8):
            mock_element = AsyncMock()
            mock_element.text_content.return_value = f"商品 {i + 1}"
            mock_product_elements.append(mock_element)

        mock_page.query_selector_all.return_value = mock_product_elements

        with (
            patch(
                "modules.scraper.yahoo_scraper.async_playwright",
                return_value=mock_playwright["async_pw_instance"],
            ),
            patch("modules.scraper.yahoo_scraper.logger") as mock_logger,
        ):
            # When: fetch_seller_productsを呼び出し
            result = await yahoo_scraper.fetch_seller_products(seller_url)

            # Then: 8件の商品情報が返される
            assert len(result["product_titles"]) == 8
            assert result["product_titles"][0] == "商品 1"

            # Then: 警告ログが記録される
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "商品数が12件未満です" in warning_call

        # クリーンアップ
        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_products_zero_items(self, yahoo_scraper, mock_playwright):
        """境界値: 0件の商品を取得"""
        # Given: モックされたPlaywrightと0件の商品
        seller_url = "https://auctions.yahoo.co.jp/sellinglist/empty_seller"
        mock_page = mock_playwright["page"]

        mock_seller_name_element = AsyncMock()
        mock_seller_name_element.text_content.return_value = "空セラー"
        mock_page.query_selector.return_value = mock_seller_name_element

        # 0件の商品
        mock_page.query_selector_all.return_value = []

        with (
            patch(
                "modules.scraper.yahoo_scraper.async_playwright",
                return_value=mock_playwright["async_pw_instance"],
            ),
            patch("modules.scraper.yahoo_scraper.logger") as mock_logger,
        ):
            # When: fetch_seller_productsを呼び出し
            result = await yahoo_scraper.fetch_seller_products(seller_url)

            # Then: 0件の商品情報が返される
            assert len(result["product_titles"]) == 0

            # Then: 警告ログが記録される
            mock_logger.warning.assert_called_once()

        # クリーンアップ
        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_products_retry_logic_success_on_second_attempt(
        self, yahoo_scraper, mock_playwright
    ):
        """正常系: 2回目のリトライで成功する"""
        # Given: 1回目は失敗、2回目は成功
        seller_url = "https://auctions.yahoo.co.jp/sellinglist/flaky_seller"
        mock_page = mock_playwright["page"]

        # 1回目は例外、2回目は成功
        attempt_counter = {"count": 0}

        async def side_effect_goto(*args, **kwargs):
            attempt_counter["count"] += 1
            if attempt_counter["count"] == 1:
                raise TimeoutError("First attempt timeout")
            # 2回目は成功（何もしない）

        mock_page.goto.side_effect = side_effect_goto

        # 2回目の成功時のモック
        mock_seller_name_element = AsyncMock()
        mock_seller_name_element.text_content.return_value = "リトライ成功セラー"
        mock_page.query_selector.return_value = mock_seller_name_element

        mock_product_elements = []
        for i in range(12):
            mock_element = AsyncMock()
            mock_element.text_content.return_value = f"商品 {i + 1}"
            mock_product_elements.append(mock_element)

        mock_page.query_selector_all.return_value = mock_product_elements

        with (
            patch(
                "modules.scraper.yahoo_scraper.async_playwright",
                return_value=mock_playwright["async_pw_instance"],
            ),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            # When: fetch_seller_productsを呼び出し
            result = await yahoo_scraper.fetch_seller_products(seller_url)

            # Then: 2回目で成功し、商品情報が返される
            assert len(result["product_titles"]) == 12
            assert attempt_counter["count"] == 2

            # Then: リトライ待機が呼ばれた（1秒待機）
            mock_sleep.assert_called_once_with(1)

        # クリーンアップ
        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_products_retry_logic_all_failures(
        self, yahoo_scraper, mock_playwright
    ):
        """異常系: 3回すべてのリトライが失敗し、ConnectionErrorが発生"""
        # Given: すべてのリトライが失敗
        seller_url = "https://auctions.yahoo.co.jp/sellinglist/always_fail"
        mock_page = mock_playwright["page"]
        mock_page.goto.side_effect = TimeoutError("Connection timeout")

        with (
            patch(
                "modules.scraper.yahoo_scraper.async_playwright",
                return_value=mock_playwright["async_pw_instance"],
            ),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            # When/Then: ConnectionErrorが発生
            with pytest.raises(ConnectionError) as exc_info:
                await yahoo_scraper.fetch_seller_products(seller_url)

            # Then: エラーメッセージに「3回のリトライ失敗」が含まれる
            assert "3回のリトライ" in str(exc_info.value)

            # Then: exponential backoffが実行された（1s, 2s）
            # 注: 3回目の試行後はリトライしないため、sleep呼び出しは2回のみ
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(1)
            mock_sleep.assert_any_call(2)

        # クリーンアップ
        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_products_exponential_backoff_timing(
        self, yahoo_scraper, mock_playwright
    ):
        """正常系: exponential backoffのタイミングが正しい（1s, 2s, 4s）"""
        # Given: すべてのリトライが失敗
        seller_url = "https://auctions.yahoo.co.jp/sellinglist/test"
        mock_page = mock_playwright["page"]
        mock_page.goto.side_effect = TimeoutError("Timeout")

        with (
            patch(
                "modules.scraper.yahoo_scraper.async_playwright",
                return_value=mock_playwright["async_pw_instance"],
            ),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            # When: ConnectionErrorが発生するまで実行
            with pytest.raises(ConnectionError):
                await yahoo_scraper.fetch_seller_products(seller_url)

            # Then: backoffタイミングが正しい
            # 注: 3回目の試行後はリトライしないため、sleep呼び出しは2回のみ
            assert mock_sleep.call_count == 2
            call_args_list = [call[0][0] for call in mock_sleep.call_args_list]
            assert call_args_list == [1, 2]

        # クリーンアップ
        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_products_max_products_parameter(
        self, yahoo_scraper, mock_playwright
    ):
        """正常系: max_productsパラメータが正しく適用される"""
        # Given: max_products=5を指定
        seller_url = "https://auctions.yahoo.co.jp/sellinglist/test"
        mock_page = mock_playwright["page"]

        mock_seller_name_element = AsyncMock()
        mock_seller_name_element.text_content.return_value = "カスタム上限セラー"
        mock_page.query_selector.return_value = mock_seller_name_element

        # 10件の商品をモック（max_products=5なので5件のみ返される）
        mock_product_elements = []
        for i in range(10):
            mock_element = AsyncMock()
            mock_element.text_content.return_value = f"商品 {i + 1}"
            mock_product_elements.append(mock_element)

        mock_page.query_selector_all.return_value = mock_product_elements

        with patch(
            "modules.scraper.yahoo_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            # When: max_products=5で呼び出し
            result = await yahoo_scraper.fetch_seller_products(seller_url, max_products=5)

            # Then: 5件のみ返される
            assert len(result["product_titles"]) == 5
            assert result["product_titles"][0] == "商品 1"
            assert result["product_titles"][4] == "商品 5"

        # クリーンアップ
        await yahoo_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_products_default_max_products(self, yahoo_scraper, mock_playwright):
        """正常系: max_productsのデフォルト値が12であることを確認"""
        # Given: max_productsを指定しない
        seller_url = "https://auctions.yahoo.co.jp/sellinglist/test"
        mock_page = mock_playwright["page"]

        mock_seller_name_element = AsyncMock()
        mock_seller_name_element.text_content.return_value = "デフォルト上限セラー"
        mock_page.query_selector.return_value = mock_seller_name_element

        # 20件の商品をモック（max_products=12なので12件のみ返される）
        mock_product_elements = []
        for i in range(20):
            mock_element = AsyncMock()
            mock_element.text_content.return_value = f"商品 {i + 1}"
            mock_product_elements.append(mock_element)

        mock_page.query_selector_all.return_value = mock_product_elements

        with patch(
            "modules.scraper.yahoo_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            # When: max_productsを指定せずに呼び出し
            result = await yahoo_scraper.fetch_seller_products(seller_url)

            # Then: 12件のみ返される（デフォルト値）
            assert len(result["product_titles"]) == 12

        # クリーンアップ
        await yahoo_scraper.close()
