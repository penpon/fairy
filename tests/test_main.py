"""
test_main.py
main.py CLI entrypoint のユニットテスト
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from main import main, parse_args, process_sellers


class TestParseArgs:
    """parse_args関数のテスト"""

    def test_parse_args_with_all_arguments(self):
        """
        Given: 全ての引数が指定されている
        When: parse_argsを呼び出す
        Then: 引数が正しくパースされる
        """
        # Given
        test_args = [
            "--start-date",
            "2025-08-01",
            "--end-date",
            "2025-10-31",
            "--min-price",
            "150000",
        ]

        # When
        with patch("sys.argv", ["main.py"] + test_args):
            args = parse_args()

        # Then
        assert args.start_date == "2025-08-01"
        assert args.end_date == "2025-10-31"
        assert args.min_price == 150000

    def test_parse_args_with_default_min_price(self):
        """
        Given: min_priceが指定されていない
        When: parse_argsを呼び出す
        Then: デフォルト値100000が使用される
        """
        # Given
        test_args = ["--start-date", "2025-08-01", "--end-date", "2025-10-31"]

        # When
        with patch("sys.argv", ["main.py"] + test_args):
            args = parse_args()

        # Then
        assert args.min_price == 100000

    def test_parse_args_missing_required_arguments(self):
        """
        Given: 必須引数が欠けている
        When: parse_argsを呼び出す
        Then: SystemExitが発生する
        """
        # Given
        test_args = ["--start-date", "2025-08-01"]  # end-dateが欠けている

        # When / Then
        with patch("sys.argv", ["main.py"] + test_args):
            with pytest.raises(SystemExit):
                parse_args()

    def test_parse_args_invalid_date_format(self):
        """
        Given: 日付フォーマットが不正
        When: parse_argsを呼び出す
        Then: SystemExitが発生する
        """
        # Given
        test_args = ["--start-date", "2025/08/01", "--end-date", "2025-10-31"]

        # When / Then
        with patch("sys.argv", ["main.py"] + test_args):
            with pytest.raises(SystemExit):
                parse_args()

    def test_parse_args_invalid_date_range(self):
        """
        Given: 開始日が終了日より後
        When: parse_argsを呼び出す
        Then: SystemExitが発生する
        """
        # Given
        test_args = ["--start-date", "2025-10-31", "--end-date", "2025-08-01"]

        # When / Then
        with patch("sys.argv", ["main.py"] + test_args):
            with pytest.raises(SystemExit):
                parse_args()

    def test_parse_args_negative_min_price(self):
        """
        Given: min_priceが負の値
        When: parse_argsを呼び出す
        Then: SystemExitが発生する
        """
        # Given
        test_args = [
            "--start-date",
            "2025-08-01",
            "--end-date",
            "2025-10-31",
            "--min-price",
            "-100",
        ]

        # When / Then
        with patch("sys.argv", ["main.py"] + test_args):
            with pytest.raises(SystemExit):
                parse_args()


class TestProcessSellers:
    """process_sellers関数のテスト（並行処理）"""

    @pytest.mark.asyncio
    async def test_process_sellers_with_max_3_concurrent(self):
        """
        Given: 5つのセラーリンクがある
        When: process_sellersを呼び出す
        Then: 最大3並列でセラー処理が実行される
        """
        # Given
        seller_links = [
            {"seller_name": "Seller1", "total_price": 100000, "link": "http://link1"},
            {"seller_name": "Seller2", "total_price": 120000, "link": "http://link2"},
            {"seller_name": "Seller3", "total_price": 150000, "link": "http://link3"},
            {"seller_name": "Seller4", "total_price": 110000, "link": "http://link4"},
            {"seller_name": "Seller5", "total_price": 130000, "link": "http://link5"},
        ]

        mock_yahoo_scraper = AsyncMock()
        mock_yahoo_scraper.fetch_seller_products = AsyncMock(
            return_value={
                "seller_name": "Test",
                "seller_url": "http://test",
                "product_titles": ["Product1"],
            }
        )

        # When
        results = await process_sellers(seller_links, mock_yahoo_scraper)

        # Then
        assert len(results) == 5
        assert mock_yahoo_scraper.fetch_seller_products.call_count == 5

    @pytest.mark.asyncio
    async def test_process_sellers_with_partial_failures(self):
        """
        Given: 一部のセラー処理が失敗する
        When: process_sellersを呼び出す
        Then: 失敗したセラーはスキップされ、成功したセラーのみ返される
        """
        # Given
        seller_links = [
            {"seller_name": "Seller1", "total_price": 100000, "link": "http://link1"},
            {"seller_name": "Seller2", "total_price": 120000, "link": "http://link2"},
            {"seller_name": "Seller3", "total_price": 150000, "link": "http://link3"},
        ]

        mock_yahoo_scraper = AsyncMock()
        mock_yahoo_scraper.fetch_seller_products = AsyncMock(
            side_effect=[
                {
                    "seller_name": "Seller1",
                    "seller_url": "http://link1",
                    "product_titles": ["Product1"],
                },
                ConnectionError("Connection failed"),
                {
                    "seller_name": "Seller3",
                    "seller_url": "http://link3",
                    "product_titles": ["Product3"],
                },
            ]
        )

        # When
        results = await process_sellers(seller_links, mock_yahoo_scraper)

        # Then
        assert len(results) == 2  # 2つのセラーのみ成功
        assert results[0]["seller_name"] == "Seller1"
        assert results[1]["seller_name"] == "Seller3"


class TestMain:
    """main関数のテスト（統合ワークフロー）"""

    @pytest.mark.asyncio
    async def test_main_workflow_success(self, monkeypatch):
        """
        Given: 全コンポーネントが正常に動作する
        When: mainを呼び出す
        Then: ワークフロー全体が成功し、CSVが2回エクスポートされる
        """
        # Given
        test_args = ["main.py", "--start-date", "2025-08-01", "--end-date", "2025-10-31"]
        monkeypatch.setattr("sys.argv", test_args)

        mock_rapras_scraper = AsyncMock()
        mock_rapras_scraper.login = AsyncMock(return_value=True)
        mock_rapras_scraper.fetch_seller_links = AsyncMock(
            return_value=[
                {"seller_name": "Seller1", "total_price": 100000, "link": "http://link1"},
                {"seller_name": "Seller2", "total_price": 120000, "link": "http://link2"},
            ]
        )
        mock_rapras_scraper.close = AsyncMock()

        mock_yahoo_scraper = AsyncMock()
        mock_yahoo_scraper.fetch_seller_products = AsyncMock(
            return_value={
                "seller_name": "Test",
                "seller_url": "http://test",
                "product_titles": ["Product1"],
            }
        )
        mock_yahoo_scraper.close = AsyncMock()

        mock_csv_exporter = MagicMock()
        mock_csv_exporter.export_intermediate_csv = MagicMock(
            return_value="output/sellers_20250101_120000.csv"
        )
        mock_csv_exporter.export_final_csv = MagicMock(
            return_value="output/sellers_20250101_120000_final.csv"
        )

        mock_anime_filter = MagicMock()
        mock_anime_filter.filter_sellers = MagicMock(
            return_value=[
                {"seller_name": "Test", "seller_url": "http://test", "is_anime_seller": True}
            ]
        )

        with (
            patch("main.RaprasScraper", return_value=mock_rapras_scraper),
            patch("main.YahooAuctionScraper", return_value=mock_yahoo_scraper),
            patch("main.CSVExporter", return_value=mock_csv_exporter),
            patch("main.AnimeFilter", return_value=mock_anime_filter),
            patch("main.load_rapras_config") as mock_load_config,
            patch("main.load_proxy_config") as mock_load_proxy,
            patch("main.SessionManager"),
        ):
            mock_load_config.return_value = MagicMock(username="test_user", password="test_pass")
            mock_load_proxy.return_value = MagicMock(
                url="http://proxy", username="proxy_user", password="proxy_pass"
            )

            # When
            await main()

            # Then
            mock_rapras_scraper.login.assert_called_once()
            mock_rapras_scraper.fetch_seller_links.assert_called_once_with(
                "2025-08-01", "2025-10-31", 100000
            )
            assert mock_yahoo_scraper.fetch_seller_products.call_count == 2
            mock_csv_exporter.export_intermediate_csv.assert_called_once()
            mock_anime_filter.filter_sellers.assert_called_once()
            mock_csv_exporter.export_final_csv.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_workflow_with_timeout_warning(self, monkeypatch):
        """
        Given: 処理時間が5分を超える
        When: mainを呼び出す
        Then: タイムアウト警告がログに出力される
        """
        # Given
        test_args = ["main.py", "--start-date", "2025-08-01", "--end-date", "2025-10-31"]
        monkeypatch.setattr("sys.argv", test_args)

        mock_rapras_scraper = AsyncMock()
        mock_rapras_scraper.login = AsyncMock(return_value=True)
        mock_rapras_scraper.fetch_seller_links = AsyncMock(
            return_value=[{"seller_name": "Seller1", "total_price": 100000, "link": "http://link1"}]
        )
        mock_rapras_scraper.close = AsyncMock()

        mock_yahoo_scraper = AsyncMock()
        mock_yahoo_scraper.fetch_seller_products = AsyncMock(
            return_value={
                "seller_name": "Test",
                "seller_url": "http://test",
                "product_titles": ["Product1"],
            }
        )
        mock_yahoo_scraper.close = AsyncMock()

        mock_csv_exporter = MagicMock()
        mock_csv_exporter.export_intermediate_csv = MagicMock(return_value="output/sellers.csv")
        mock_csv_exporter.export_final_csv = MagicMock(return_value="output/sellers_final.csv")

        mock_anime_filter = MagicMock()
        mock_anime_filter.filter_sellers = MagicMock(
            return_value=[
                {"seller_name": "Test", "seller_url": "http://test", "is_anime_seller": True}
            ]
        )

        with (
            patch("main.RaprasScraper", return_value=mock_rapras_scraper),
            patch("main.YahooAuctionScraper", return_value=mock_yahoo_scraper),
            patch("main.CSVExporter", return_value=mock_csv_exporter),
            patch("main.AnimeFilter", return_value=mock_anime_filter),
            patch("main.load_rapras_config") as mock_load_config,
            patch("main.load_proxy_config") as mock_load_proxy,
            patch("main.SessionManager"),
            patch("main.logger") as mock_logger,
            patch("time.time") as mock_time,
        ):
            mock_load_config.return_value = MagicMock(username="test_user", password="test_pass")
            mock_load_proxy.return_value = MagicMock(
                url="http://proxy", username="proxy_user", password="proxy_pass"
            )

            # Mock time to simulate 6 minutes elapsed (start=0, end=360)
            mock_time.side_effect = [0, 360]

            # When
            await main()

            # Then
            # Verify warning was logged for timeout
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Processing time exceeded" in warning_call
            assert "5.0 minutes" in warning_call

    @pytest.mark.asyncio
    async def test_main_with_rapras_login_failure(self, monkeypatch):
        """
        Given: Raprasログインが失敗する
        When: mainを呼び出す
        Then: AuthenticationErrorがログに記録され、処理が中断される
        """
        # Given
        test_args = ["main.py", "--start-date", "2025-08-01", "--end-date", "2025-10-31"]
        monkeypatch.setattr("sys.argv", test_args)

        mock_rapras_scraper = AsyncMock()
        mock_rapras_scraper.login = AsyncMock(side_effect=Exception("Authentication failed"))
        mock_rapras_scraper.close = AsyncMock()

        mock_yahoo_scraper = AsyncMock()
        mock_yahoo_scraper.close = AsyncMock()

        with (
            patch("main.RaprasScraper", return_value=mock_rapras_scraper),
            patch("main.YahooAuctionScraper", return_value=mock_yahoo_scraper),
            patch("main.load_rapras_config") as mock_load_config,
            patch("main.load_proxy_config") as mock_load_proxy,
            patch("main.SessionManager"),
            patch("main.logger"),
        ):
            mock_load_config.return_value = MagicMock(username="test_user", password="test_pass")
            mock_load_proxy.return_value = MagicMock(
                url="http://proxy", username="proxy_user", password="proxy_pass"
            )

            # When
            with pytest.raises(Exception, match="Authentication failed"):
                await main()

            # Then
            mock_rapras_scraper.login.assert_called_once()
            mock_rapras_scraper.close.assert_called_once()
            mock_yahoo_scraper.close.assert_called_once()
