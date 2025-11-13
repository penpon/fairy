"""
End-to-End Integration Tests for Seller Data Collection Analysis Workflow

This module tests the full workflow from Rapras login to final CSV export,
mocking external services while testing real module integration.

Test Scenarios:
1. Partial failure: Some sellers fail Yahoo Auctions
2. Gemini API errors: Continue processing despite errors
3. Parallel processing: Max 3 concurrent sellers
4. Timeout warning: Processing time > 5 minutes
5. CSV format verification: Intermediate vs Final CSV structure
"""

import asyncio
import logging
import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from main import main, process_sellers
from modules.analyzer.anime_filter import AnimeFilter
from modules.scraper.session_manager import SessionManager
from modules.scraper.yahoo_scraper import YahooAuctionScraper
from modules.storage.csv_exporter import CSVExporter


@pytest.mark.asyncio
async def test_e2e_partial_failure():
    """
    Test Scenario 1: Partial failure during seller data collection.

    Verifies that the workflow gracefully handles Yahoo Auctions connection failures
    for some sellers while successfully processing others. This ensures the system's
    resilience and error recovery capabilities.

    Given: 10 sellers, 3 fail Yahoo Auctions connection
    When: process_sellers() executes with error handling
    Then: 7 sellers are processed successfully and 3 failures are logged

    Args:
        None (uses mocked YahooAuctionScraper)

    Returns:
        None (assertions verify expected behavior)
    """
    # Given: Prepare test data - 10 seller links
    seller_links = [
        {
            "seller_name": f"セラー{i}",
            "link": f"https://auctions.yahoo.co.jp/seller{i}",
        }
        for i in range(1, 11)
    ]

    # Given: Mock YahooAuctionScraper to fail for sellers 3, 6, 9
    async def mock_fetch_seller_products(seller_url: str):
        seller_num = int(seller_url.split("seller")[-1])
        if seller_num in [3, 6, 9]:
            raise ConnectionError(f"Failed to fetch {seller_url}")
        return {
            "seller_name": f"セラー{seller_num}",
            "seller_url": seller_url,
            "product_titles": [f"商品{seller_num}-1", f"商品{seller_num}-2"],
        }

    # When: Process sellers with error handling
    with patch.object(
        YahooAuctionScraper, "fetch_seller_products", new_callable=AsyncMock
    ) as mock_yahoo:
        mock_yahoo.side_effect = mock_fetch_seller_products

        session_manager = SessionManager()
        proxy_config = {
            "url": "http://proxy.example.com:3128",
            "username": "user",
            "password": "pass",
        }
        yahoo_scraper = YahooAuctionScraper(session_manager, proxy_config)

        try:
            sellers = await process_sellers(seller_links, yahoo_scraper)
        finally:
            await yahoo_scraper.close()

    # Then: Verify only 7 sellers processed successfully
    assert len(sellers) == 7
    assert all(s["seller_name"] not in ["セラー3", "セラー6", "セラー9"] for s in sellers)


@pytest.mark.asyncio
async def test_e2e_gemini_api_errors(tmp_path):
    """
    Test Scenario 2: Gemini API error handling during anime filtering.

    Validates that when Gemini CLI encounters errors (e.g., API rate limits,
    network issues), the workflow continues processing and marks affected
    sellers as non-anime (False) rather than failing the entire pipeline.

    Given: Gemini CLI raises CalledProcessError exceptions
    When: AnimeFilter.filter_sellers() processes sellers
    Then: Processing continues without interruption, and sellers are marked
          as is_anime_seller=False and exported as "いいえ" in CSV

    Args:
        tmp_path: pytest fixture providing temporary directory for CSV output

    Returns:
        None (assertions verify expected behavior)
    """
    # Given: Prepare test data
    sellers = [
        {
            "seller_name": "セラー1",
            "seller_url": "https://auctions.yahoo.co.jp/seller1",
            "product_titles": ["商品1", "商品2"],
        }
    ]

    # When: Filter sellers with Gemini errors
    with patch("subprocess.run") as mock_subprocess:
        # Mock subprocess.CalledProcessError (which is raised when check=True fails)
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["gemini"], stderr="Gemini API error"
        )

        anime_filter = AnimeFilter()
        filtered_sellers = anime_filter.filter_sellers(sellers)

    # Then: Verify seller is marked False (Gemini errors are logged but processing continues)
    # Note: Implementation marks as False when all products fail, not None
    assert len(filtered_sellers) == 1
    assert filtered_sellers[0].get("is_anime_seller") is False

    # Then: Export to CSV and verify "いいえ" (not "未判定")
    csv_exporter = CSVExporter(output_dir=str(tmp_path))
    final_csv = csv_exporter.export_final_csv(filtered_sellers)

    final_df = pd.read_csv(final_csv)
    assert len(final_df) == 1
    assert final_df["二次創作"].values[0] == "いいえ"


@pytest.mark.asyncio
async def test_e2e_parallel_processing():
    """
    Test Scenario 3: Parallel processing with concurrency limits.

    Verifies that the system properly enforces the maximum concurrent seller
    processing limit (MAX_CONCURRENT_SELLERS=3) using asyncio.Semaphore to
    prevent overwhelming external services (Yahoo Auctions).

    Given: 5 sellers to process concurrently
    When: process_sellers() executes with semaphore(3)
    Then: Maximum 3 concurrent executions occur at any given time, and all
          5 sellers are processed successfully

    Args:
        None (uses mocked YahooAuctionScraper)

    Returns:
        None (assertions verify expected behavior)
    """
    # Given: Track concurrent execution count
    concurrent_count = 0
    max_concurrent = 0

    async def mock_fetch(seller_url):
        nonlocal concurrent_count, max_concurrent
        concurrent_count += 1
        max_concurrent = max(max_concurrent, concurrent_count)
        await asyncio.sleep(0.1)  # Simulate work
        concurrent_count -= 1

        return {
            "seller_name": seller_url.split("/")[-1],
            "seller_url": seller_url,
            "product_titles": ["商品1"],
        }

    # When: Process with semaphore
    seller_links = [
        {
            "seller_name": f"セラー{i}",
            "link": f"https://auctions.yahoo.co.jp/seller{i}",
        }
        for i in range(1, 6)
    ]

    with patch.object(
        YahooAuctionScraper, "fetch_seller_products", new_callable=AsyncMock
    ) as mock_yahoo:
        mock_yahoo.side_effect = mock_fetch

        session_manager = SessionManager()
        proxy_config = {
            "url": "http://proxy.example.com:3128",
            "username": "user",
            "password": "pass",
        }
        yahoo_scraper = YahooAuctionScraper(session_manager, proxy_config)

        try:
            sellers = await process_sellers(seller_links, yahoo_scraper)
        finally:
            await yahoo_scraper.close()

    # Then: Verify max 3 concurrent
    assert max_concurrent <= 3
    assert len(sellers) == 5


@pytest.fixture
def mock_main_dependencies(tmp_path):
    """
    Fixture providing mocked dependencies for main() function.

    Returns a dictionary containing mocked configurations and instances:
    - rapras_config: Mock RaprasConfig
    - proxy_config: Mock ProxyConfig
    - rapras_instance: AsyncMock RaprasScraper instance
    - yahoo_instance: AsyncMock YahooAuctionScraper instance
    - anime_filter: Mock AnimeFilter instance
    - csv_exporter: Mock CSVExporter instance
    """
    mocks = {
        "rapras_config": MagicMock(username="user", password="pass"),
        "proxy_config": MagicMock(
            url="http://proxy.example.com:3128", username="proxy_user", password="proxy_pass"
        ),
    }

    # Mock Rapras scraper
    rapras_instance = AsyncMock()
    rapras_instance.login = AsyncMock()
    rapras_instance.fetch_seller_links = AsyncMock(
        return_value=[{"seller_name": "セラー1", "link": "https://auctions.yahoo.co.jp/seller1"}]
    )
    rapras_instance.close = AsyncMock()
    mocks["rapras_instance"] = rapras_instance

    # Mock Yahoo scraper
    yahoo_instance = AsyncMock()
    yahoo_instance.fetch_seller_products = AsyncMock(
        return_value={
            "seller_name": "セラー1",
            "seller_url": "https://auctions.yahoo.co.jp/seller1",
            "product_titles": ["商品1"],
        }
    )
    yahoo_instance.close = AsyncMock()
    mocks["yahoo_instance"] = yahoo_instance

    # Mock AnimeFilter
    anime_filter = MagicMock()
    anime_filter.filter_sellers = MagicMock(
        return_value=[
            {
                "seller_name": "セラー1",
                "seller_url": "https://auctions.yahoo.co.jp/seller1",
                "is_anime_seller": True,
            }
        ]
    )
    mocks["anime_filter"] = anime_filter

    # Mock CSVExporter
    csv_exporter = MagicMock()
    csv_exporter.export_intermediate_csv = MagicMock(
        return_value=str(tmp_path / "intermediate.csv")
    )
    csv_exporter.export_final_csv = MagicMock(return_value=str(tmp_path / "final.csv"))
    mocks["csv_exporter"] = csv_exporter

    return mocks


@pytest.mark.asyncio
async def test_e2e_timeout_warning(caplog, monkeypatch, tmp_path, mock_main_dependencies):
    """
    Test Scenario 4: Timeout warning for long-running workflows.

    Ensures that when the entire workflow execution exceeds the 5-minute
    threshold (300 seconds), a warning is logged to alert operators while
    allowing the processing to complete normally.

    Given: Workflow execution time exceeds 5 minutes (simulated via time.time mock)
    When: main() executes from start to finish
    Then: A warning "Processing time exceeded 5 minutes" is logged, and
          processing continues to completion

    Args:
        caplog: pytest fixture for capturing log messages
        monkeypatch: pytest fixture for modifying sys.argv
        tmp_path: pytest fixture providing temporary directory
        mock_main_dependencies: Custom fixture providing mocked dependencies

    Returns:
        None (assertions verify expected behavior)
    """
    # Given: Mock command line arguments
    test_args = [
        "main.py",
        "--start-date",
        "2025-08-01",
        "--end-date",
        "2025-10-31",
    ]
    monkeypatch.setattr("sys.argv", test_args)

    # Given: Mock time.time() to simulate > 300 seconds elapsed
    # main.py calls time.time() twice: once at start, once at end
    start_time = 0.0
    end_time = 310.0

    call_count = {"count": 0}

    def mock_time():
        call_count["count"] += 1
        if call_count["count"] == 1:
            return start_time
        return end_time

    # When: Execute main() with mocked dependencies
    with patch("time.time", side_effect=mock_time):
        with patch("main.load_rapras_config", return_value=mock_main_dependencies["rapras_config"]):
            with patch(
                "main.load_proxy_config", return_value=mock_main_dependencies["proxy_config"]
            ):
                with patch(
                    "main.RaprasScraper", return_value=mock_main_dependencies["rapras_instance"]
                ):
                    with patch(
                        "main.YahooAuctionScraper",
                        return_value=mock_main_dependencies["yahoo_instance"],
                    ):
                        with patch(
                            "main.AnimeFilter", return_value=mock_main_dependencies["anime_filter"]
                        ):
                            with patch(
                                "main.CSVExporter",
                                return_value=mock_main_dependencies["csv_exporter"],
                            ):
                                caplog.set_level(logging.WARNING, logger="main")
                                await main()

    # Then: Verify timeout warning was logged
    assert any(
        "Processing time exceeded" in record.message and record.levelname == "WARNING"
        for record in caplog.records
    )


@pytest.mark.asyncio
async def test_e2e_csv_format_verification(tmp_path):
    """
    Test Scenario 5: CSV format verification for intermediate and final outputs.

    Validates that the CSV export process correctly formats the "二次創作"
    (anime derivative work) column differently in intermediate vs final CSVs:
    - Intermediate CSV: "未判定" (undetermined) for all sellers
    - Final CSV: "はい" (yes) or "いいえ" (no) based on is_anime_seller flag

    This ensures proper data flow through the pipeline and correct output
    formatting for downstream consumers.

    Given: Sellers with anime判定 results (True/False)
    When: CSVExporter exports both intermediate and final CSVs
    Then: Intermediate CSV contains "未判定" for all entries, and
          Final CSV contains "はい" for True and "いいえ" for False

    Args:
        tmp_path: pytest fixture providing temporary directory for CSV output

    Returns:
        None (assertions verify expected behavior)
    """
    # Given: Prepare test data
    intermediate_sellers = [
        {
            "seller_name": "セラー1",
            "seller_url": "https://auctions.yahoo.co.jp/seller1",
            "product_titles": ["商品1", "商品2"],
        },
        {
            "seller_name": "セラー2",
            "seller_url": "https://auctions.yahoo.co.jp/seller2",
            "product_titles": ["商品3", "商品4"],
        },
    ]

    final_sellers = [
        {
            "seller_name": "セラー1",
            "seller_url": "https://auctions.yahoo.co.jp/seller1",
            "is_anime_seller": True,
        },
        {
            "seller_name": "セラー2",
            "seller_url": "https://auctions.yahoo.co.jp/seller2",
            "is_anime_seller": False,
        },
    ]

    # When: Export CSVs
    csv_exporter = CSVExporter(output_dir=str(tmp_path))
    intermediate_csv = csv_exporter.export_intermediate_csv(intermediate_sellers)
    final_csv = csv_exporter.export_final_csv(final_sellers)

    # Then: Verify intermediate CSV contains "未判定"
    intermediate_df = pd.read_csv(intermediate_csv)
    assert len(intermediate_df) == 2
    assert all(intermediate_df["二次創作"] == "未判定")

    # Then: Verify final CSV contains "はい"/"いいえ"
    final_df = pd.read_csv(final_csv)
    assert len(final_df) == 2
    assert final_df["二次創作"].values[0] == "はい"
    assert final_df["二次創作"].values[1] == "いいえ"
