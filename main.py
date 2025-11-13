"""
main.py
Yahoo Auction Seller Data Collection CLI Entrypoint

Workflow:
1. Rapras login → Fetch seller links
2. Parallel fetch products (max 3 concurrent)
3. Export intermediate CSV
4. Anime filter
5. Export final CSV
"""

import argparse
import asyncio
import time
from typing import Any

from modules.analyzer.anime_filter import AnimeFilter
from modules.config.constants import (
    MAX_CONCURRENT_SELLERS,
    MIN_SELLER_PRICE,
    TIMEOUT_WARNING_SECONDS,
)
from modules.config.settings import load_proxy_config, load_rapras_config
from modules.scraper.rapras_scraper import RaprasScraper
from modules.scraper.session_manager import SessionManager
from modules.scraper.yahoo_scraper import YahooAuctionScraper
from modules.storage.csv_exporter import CSVExporter
from modules.utils.logger import get_logger

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Yahoo Auction Seller Data Collection and Anime Filtering"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--min-price",
        type=int,
        default=MIN_SELLER_PRICE,
        help=f"Minimum seller total price (default: {MIN_SELLER_PRICE})",
    )
    return parser.parse_args()


async def process_sellers(
    seller_links: list[dict[str, Any]], yahoo_scraper: YahooAuctionScraper
) -> list[dict[str, Any]]:
    """
    Process sellers in parallel (max 3 concurrent)

    Args:
        seller_links: List of seller links from Rapras
        yahoo_scraper: YahooAuctionScraper instance

    Returns:
        list[dict]: List of seller data with product titles
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_SELLERS)
    results: list[dict[str, Any]] = []

    async def process_one_seller(seller: dict[str, Any]) -> dict[str, Any] | None:
        """Process a single seller with semaphore"""
        async with semaphore:
            try:
                logger.info(f"Processing seller: {seller['seller_name']}")
                seller_data = await yahoo_scraper.fetch_seller_products(seller["link"])
                return seller_data
            except Exception as e:
                logger.warning(f"Failed to process seller {seller['seller_name']}: {e}")
                return None

    # Create tasks for all sellers
    tasks = [process_one_seller(seller) for seller in seller_links]

    # Run tasks concurrently with return_exceptions=True
    completed_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out None and Exception results
    for result in completed_results:
        if result is not None and not isinstance(result, Exception):
            results.append(result)

    return results


async def main() -> None:
    """
    Main workflow orchestration

    Workflow:
    1. Parse CLI arguments
    2. Rapras login
    3. Fetch seller links from Rapras
    4. Parallel fetch products from Yahoo Auctions (max 3 concurrent)
    5. Export intermediate CSV
    6. Anime filter
    7. Export final CSV
    """
    start_time = time.time()

    # Step 1: Parse CLI arguments
    args = parse_args()
    logger.info("=" * 50)
    logger.info("Yahoo Auction Seller Data Collection")
    logger.info(f"Start Date: {args.start_date}")
    logger.info(f"End Date: {args.end_date}")
    logger.info(f"Min Price: {args.min_price}")
    logger.info("=" * 50)

    # Step 2: Initialize scrapers
    logger.info("Step 1: Initialize scrapers")
    rapras_config = load_rapras_config()
    proxy_config = load_proxy_config()
    session_manager = SessionManager()

    # Initialize scrapers to None for safe cleanup
    rapras_scraper = None
    yahoo_scraper = None

    try:
        # Create scrapers
        rapras_scraper = RaprasScraper(rapras_config.username, rapras_config.password)
        yahoo_scraper = YahooAuctionScraper(
            session_manager=session_manager,
            proxy_config={
                "url": proxy_config.url,
                "username": proxy_config.username,
                "password": proxy_config.password,
            },
        )
        await rapras_scraper.login()
        logger.info("✅ Rapras login successful")

        # Step 3: Fetch seller links
        logger.info("Step 2: Fetch seller links from Rapras")
        seller_links = await rapras_scraper.fetch_seller_links(
            args.start_date, args.end_date, args.min_price
        )
        logger.info(f"Found {len(seller_links)} sellers")

        if not seller_links:
            logger.warning("No sellers found. Exiting.")
            return

        # Step 4: Parallel fetch products (max concurrent)
        logger.info(
            f"Step 3: Fetch products from Yahoo Auctions (max {MAX_CONCURRENT_SELLERS} concurrent)"
        )
        seller_data_list = await process_sellers(seller_links, yahoo_scraper)
        logger.info(
            f"Successfully fetched products from {len(seller_data_list)}/{len(seller_links)} sellers"
        )

        if not seller_data_list:
            logger.warning("No seller data fetched. Exiting.")
            return

        # Step 5: Export intermediate CSV
        logger.info("Step 4: Export intermediate CSV")
        csv_exporter = CSVExporter()
        intermediate_csv_path = csv_exporter.export_intermediate_csv(seller_data_list)
        logger.info(f"✅ Intermediate CSV exported: {intermediate_csv_path}")

        # Step 6: Anime filter
        logger.info("Step 5: Anime filter")
        anime_filter = AnimeFilter()
        filtered_sellers = anime_filter.filter_sellers(seller_data_list)
        anime_seller_count = sum(1 for seller in filtered_sellers if seller.get("is_anime_seller"))
        logger.info(f"Anime sellers: {anime_seller_count}/{len(filtered_sellers)} sellers")

        # Step 7: Export final CSV
        logger.info("Step 6: Export final CSV")
        final_csv_path = csv_exporter.export_final_csv(filtered_sellers)
        logger.info(f"✅ Final CSV exported: {final_csv_path}")

        # Check timeout warning
        elapsed_time = time.time() - start_time
        if elapsed_time > TIMEOUT_WARNING_SECONDS:
            logger.warning(
                f"⚠️ Processing time exceeded {TIMEOUT_WARNING_SECONDS / 60:.1f} minutes ({elapsed_time:.1f} seconds)"
            )

        # Success summary
        logger.info("=" * 50)
        logger.info("✅ All processing completed successfully")
        logger.info(f"Total sellers processed: {len(seller_data_list)}")
        logger.info(f"Anime sellers identified: {anime_seller_count}")
        logger.info(f"Processing time: {elapsed_time:.1f} seconds")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"❌ Error during processing: {e}")
        raise
    finally:
        # Cleanup resources
        if rapras_scraper:
            await rapras_scraper.close()
        if yahoo_scraper:
            await yahoo_scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
