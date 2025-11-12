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

        # get_by_role()のモック（Locatorオブジェクトを返す）
        # get_by_role()は同期関数でLocatorオブジェクトを返す
        mock_locator = MagicMock()
        mock_locator.click = AsyncMock()
        mock_page.get_by_role = MagicMock(return_value=mock_locator)

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
        mock_page.query_selector.return_value = (
            MagicMock()
        )  # ログアウトリンクが存在（ログイン済み）

        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            # When: ログイン
            result = await rapras_scraper.login("test_user", "test_password")

            # Then: ログインに成功
            assert result is True
            mock_page.goto.assert_called()
            assert mock_page.fill.call_count >= 2  # username と password
            mock_page.get_by_role.assert_called_with("button", name="ログイン")

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

    @pytest.mark.asyncio
    async def test_restore_session_no_cookies(self, rapras_scraper, mock_playwright):
        """異常系: セッションにCookieが存在しない場合"""
        # Given: load_sessionがNoneを返す
        with patch.object(rapras_scraper.session_manager, "load_session", return_value=None):
            # When: セッション復元を試みる
            result = await rapras_scraper._restore_session()

            # Then: Falseが返される
            assert result is False

    @pytest.mark.asyncio
    async def test_restore_session_exception(self, rapras_scraper, mock_playwright):
        """異常系: セッション復元中に例外が発生"""
        # Given: ブラウザ起動時に例外が発生
        with (
            patch.object(
                rapras_scraper.session_manager, "load_session", return_value=[{"name": "test"}]
            ),
            patch.object(
                rapras_scraper, "_launch_browser", side_effect=RuntimeError("Browser error")
            ),
        ):
            # When: セッション復元を試みる
            result = await rapras_scraper._restore_session()

            # Then: Falseが返される（例外は内部で処理される）
            assert result is False

    @pytest.mark.asyncio
    async def test_fetch_seller_links_success(self, rapras_scraper, mock_playwright):
        """正常系: fetch_seller_linksが正常にセラーリンクを取得"""
        # Given: ログイン済み、集計ページから10万円以上のセラーを取得
        mock_page = mock_playwright["page"]
        mock_page.query_selector.return_value = MagicMock()  # ログイン済み

        # モックのセラーテーブル要素
        mock_row1 = MagicMock()

        # query_selectorをAsyncMockに変更
        async def row1_query_selector(sel):
            result_map = {
                "td:nth-child(2)": AsyncMock(inner_text=AsyncMock(return_value="セラーA")),
                "td:nth-child(5)": AsyncMock(inner_text=AsyncMock(return_value="150,000円")),
                "td:nth-child(2) a": AsyncMock(
                    get_attribute=AsyncMock(
                        return_value="https://auctions.yahoo.co.jp/sellinglist/seller_a"
                    )
                ),
            }
            return result_map.get(sel)

        mock_row1.query_selector = row1_query_selector

        mock_row2 = MagicMock()

        async def row2_query_selector(sel):
            result_map = {
                "td:nth-child(2)": AsyncMock(inner_text=AsyncMock(return_value="セラーB")),
                "td:nth-child(5)": AsyncMock(inner_text=AsyncMock(return_value="80,000円")),
                "td:nth-child(2) a": AsyncMock(
                    get_attribute=AsyncMock(
                        return_value="https://auctions.yahoo.co.jp/sellinglist/seller_b"
                    )
                ),
            }
            return result_map.get(sel)

        mock_row2.query_selector = row2_query_selector

        # テーブルのモックを作成
        mock_table = MagicMock()

        async def table_query_selector(sel):
            if sel == "tbody tr":
                return mock_row1
            return None

        async def table_query_selector_all(sel):
            if sel == "tbody tr":
                return [mock_row1, mock_row2]
            return []

        mock_table.query_selector = table_query_selector
        mock_table.query_selector_all = table_query_selector_all

        # pageのquery_selector_allはtablesとして呼ばれる
        async def page_query_selector_all(sel):
            if sel == "table":
                return [mock_table]
            return []

        mock_page.query_selector_all = page_query_selector_all

        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            # ログイン
            await rapras_scraper.login("test_user", "test_password")

            # When: セラーリンクを取得
            result = await rapras_scraper.fetch_seller_links(
                start_date="2025-08-01", end_date="2025-10-31", min_price=100000
            )

            # Then: 10万円以上のセラーのみ取得
            assert len(result) == 1
            assert result[0]["seller_name"] == "セラーA"
            assert result[0]["total_price"] == 150000
            assert result[0]["link"] == "https://auctions.yahoo.co.jp/sellinglist/seller_a"

        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_links_empty(self, rapras_scraper, mock_playwright):
        """境界値: 10万円以上のセラーが0件"""
        # Given: すべてのセラーが10万円未満
        mock_page = mock_playwright["page"]
        mock_page.query_selector.return_value = MagicMock()  # ログイン済み

        mock_row = MagicMock()

        async def row_query_selector(sel):
            result_map = {
                "td:nth-child(2)": AsyncMock(inner_text=AsyncMock(return_value="セラーC")),
                "td:nth-child(5)": AsyncMock(inner_text=AsyncMock(return_value="50,000円")),
                "td:nth-child(2) a": AsyncMock(
                    get_attribute=AsyncMock(
                        return_value="https://auctions.yahoo.co.jp/sellinglist/seller_c"
                    )
                ),
            }
            return result_map.get(sel)

        mock_row.query_selector = row_query_selector

        mock_page.query_selector_all.return_value = [mock_row]

        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await rapras_scraper.login("test_user", "test_password")

            # When: セラーリンクを取得
            result = await rapras_scraper.fetch_seller_links(
                start_date="2025-08-01", end_date="2025-10-31", min_price=100000
            )

            # Then: 空のリスト
            assert len(result) == 0

        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_links_boundary_exact_min_price(
        self, rapras_scraper, mock_playwright
    ):
        """境界値: total_priceが正確に10万円のセラー"""
        # Given: total_priceが正確に100000円
        mock_page = mock_playwright["page"]
        mock_page.query_selector.return_value = MagicMock()

        mock_row = MagicMock()

        async def row_query_selector(sel):
            result_map = {
                "td:nth-child(2)": AsyncMock(inner_text=AsyncMock(return_value="セラーD")),
                "td:nth-child(5)": AsyncMock(inner_text=AsyncMock(return_value="100,000円")),
                "td:nth-child(2) a": AsyncMock(
                    get_attribute=AsyncMock(
                        return_value="https://auctions.yahoo.co.jp/sellinglist/seller_d"
                    )
                ),
            }
            return result_map.get(sel)

        mock_row.query_selector = row_query_selector

        # テーブルのモックを作成
        mock_table = MagicMock()

        async def table_query_selector(sel):
            if sel == "tbody tr":
                return mock_row
            return None

        async def table_query_selector_all(sel):
            if sel == "tbody tr":
                return [mock_row]
            return []

        mock_table.query_selector = table_query_selector
        mock_table.query_selector_all = table_query_selector_all

        # pageのquery_selector_allはtablesとして呼ばれる
        async def page_query_selector_all(sel):
            if sel == "table":
                return [mock_table]
            return []

        mock_page.query_selector_all = page_query_selector_all

        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await rapras_scraper.login("test_user", "test_password")

            # When: セラーリンクを取得
            result = await rapras_scraper.fetch_seller_links(
                start_date="2025-08-01", end_date="2025-10-31", min_price=100000
            )

            # Then: 境界値（=100000）も含まれる
            assert len(result) == 1
            assert result[0]["total_price"] == 100000

        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_links_invalid_date_format(self, rapras_scraper, mock_playwright):
        """異常系: 不正な日付フォーマット"""
        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await rapras_scraper.login("test_user", "test_password")

            # When/Then: ValueError が発生
            with pytest.raises(ValueError) as exc_info:
                await rapras_scraper.fetch_seller_links(
                    start_date="2025/08/01",  # 不正なフォーマット
                    end_date="2025-10-31",
                    min_price=100000,
                )

            assert "Invalid date format" in str(exc_info.value)

        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_links_invalid_date_range(self, rapras_scraper, mock_playwright):
        """異常系: 開始日が終了日より後"""
        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await rapras_scraper.login("test_user", "test_password")

            # When/Then: ValueError が発生
            with pytest.raises(ValueError) as exc_info:
                await rapras_scraper.fetch_seller_links(
                    start_date="2025-10-31", end_date="2025-08-01", min_price=100000
                )

            assert "start_date" in str(exc_info.value)
            assert "end_date" in str(exc_info.value)

        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_links_negative_min_price(self, rapras_scraper, mock_playwright):
        """異常系: 負の最低価格"""
        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await rapras_scraper.login("test_user", "test_password")

            # When/Then: ValueError が発生
            with pytest.raises(ValueError) as exc_info:
                await rapras_scraper.fetch_seller_links(
                    start_date="2025-08-01", end_date="2025-10-31", min_price=-1
                )

            assert "min_price must be >= 0" in str(exc_info.value)

        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_links_browser_not_initialized(self, rapras_scraper):
        """異常系: ブラウザが初期化されていない"""
        # Given: ログインせずにfetch_seller_linksを呼ぶ
        assert rapras_scraper.page is None

        # When/Then: RuntimeError が発生
        with pytest.raises(RuntimeError) as exc_info:
            await rapras_scraper.fetch_seller_links(
                start_date="2025-08-01", end_date="2025-10-31", min_price=100000
            )

        assert "Browser not initialized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_seller_links_not_logged_in(self, rapras_scraper, mock_playwright):
        """異常系: ログインしていない"""
        # Given: ブラウザは起動しているがログインしていない
        mock_page = mock_playwright["page"]
        mock_page.query_selector.return_value = None  # ログアウト状態

        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            # ブラウザのみ起動（ログインはスキップ）
            await rapras_scraper._launch_browser()

            # When/Then: RuntimeError が発生
            with pytest.raises(RuntimeError) as exc_info:
                await rapras_scraper.fetch_seller_links(
                    start_date="2025-08-01", end_date="2025-10-31", min_price=100000
                )

            assert "Not logged in" in str(exc_info.value)

        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_links_timeout(self, rapras_scraper, mock_playwright):
        """異常系: ページ読み込みタイムアウト"""
        mock_page = mock_playwright["page"]
        mock_page.query_selector.return_value = MagicMock()  # ログイン状態

        # goto() でタイムアウトを発生させる
        mock_page.goto.side_effect = TimeoutError("Navigation timeout")

        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await rapras_scraper.login("test_user", "test_password")

            # gotoのタイムアウトを再設定
            mock_page.goto.side_effect = TimeoutError("Navigation timeout")

            # When/Then: TimeoutError が再スローされる
            with pytest.raises(TimeoutError):
                await rapras_scraper.fetch_seller_links(
                    start_date="2025-08-01", end_date="2025-10-31", min_price=100000
                )

        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_links_unexpected_exception(self, rapras_scraper, mock_playwright):
        """異常系: 予期しない例外"""
        mock_page = mock_playwright["page"]
        mock_page.query_selector.return_value = MagicMock()  # ログイン状態

        # goto() で予期しない例外を発生させる
        mock_page.goto.side_effect = RuntimeError("Unexpected error")

        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await rapras_scraper.login("test_user", "test_password")

            # gotoの例外を再設定
            mock_page.goto.side_effect = RuntimeError("Unexpected error")

            # When/Then: 例外が再スローされる
            with pytest.raises(RuntimeError):
                await rapras_scraper.fetch_seller_links(
                    start_date="2025-08-01", end_date="2025-10-31", min_price=100000
                )

        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_links_no_table_found(self, rapras_scraper, mock_playwright):
        """境界値: セラーテーブルが見つからない"""
        mock_page = mock_playwright["page"]
        mock_page.query_selector.return_value = MagicMock()  # ログイン状態

        # テーブルが見つからない
        async def page_query_selector_all(sel):
            if sel == "table":
                return []  # テーブルなし
            return []

        mock_page.query_selector_all = page_query_selector_all

        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await rapras_scraper.login("test_user", "test_password")

            # When: セラーリンクを取得
            result = await rapras_scraper.fetch_seller_links(
                start_date="2025-08-01", end_date="2025-10-31", min_price=100000
            )

            # Then: 空のリスト
            assert len(result) == 0

        await rapras_scraper.close()

    @pytest.mark.asyncio
    async def test_fetch_seller_links_parse_error_in_row(self, rapras_scraper, mock_playwright):
        """異常系: 行のパース中にエラー"""
        mock_page = mock_playwright["page"]
        mock_page.query_selector.return_value = MagicMock()  # ログイン状態

        # モックの行でパースエラーを発生させる
        mock_row = MagicMock()

        async def row_query_selector(sel):
            if sel == "td:nth-child(2)":
                return AsyncMock(inner_text=AsyncMock(return_value="セラーE"))
            elif sel == "td:nth-child(5)":
                # 不正な価格フォーマット（数値に変換できない）
                return AsyncMock(inner_text=AsyncMock(return_value="不正な価格"))
            elif sel == "td:nth-child(2) a":
                return AsyncMock(
                    get_attribute=AsyncMock(
                        return_value="https://auctions.yahoo.co.jp/sellinglist/seller_e"
                    )
                )
            return None

        mock_row.query_selector = row_query_selector

        # テーブルのモックを作成
        mock_table = MagicMock()

        async def table_query_selector(sel):
            if sel == "tbody tr":
                return mock_row
            return None

        async def table_query_selector_all(sel):
            if sel == "tbody tr":
                return [mock_row]
            return []

        mock_table.query_selector = table_query_selector
        mock_table.query_selector_all = table_query_selector_all

        # pageのquery_selector_allはtablesとして呼ばれる
        async def page_query_selector_all(sel):
            if sel == "table":
                return [mock_table]
            return []

        mock_page.query_selector_all = page_query_selector_all

        with patch(
            "modules.scraper.rapras_scraper.async_playwright",
            return_value=mock_playwright["async_pw_instance"],
        ):
            await rapras_scraper.login("test_user", "test_password")

            # When: セラーリンクを取得（パースエラーは無視される）
            result = await rapras_scraper.fetch_seller_links(
                start_date="2025-08-01", end_date="2025-10-31", min_price=100000
            )

            # Then: パースエラーの行はスキップされ空のリスト
            assert len(result) == 0

        await rapras_scraper.close()
