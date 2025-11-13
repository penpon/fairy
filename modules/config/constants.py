"""
Application constants for Yahoo Auction Scraper.

This module centralizes all magic numbers and configuration values
used across the application. Constants follow UPPER_SNAKE_CASE naming
convention and must be static (no dynamic values).

Constants are grouped by functional area:
- Yahoo Auctions: Product scraping configuration
- Rapras: Web scraping configuration
- Retry Strategy: Network retry configuration
"""

# ===== Yahoo Auctions Configuration =====
# Maximum number of products to scrape per seller page
MAX_PRODUCTS_PER_SELLER: int = 12

# Proxy server for Yahoo Auctions access
# Used to avoid IP blocking and rate limiting
YAHOO_PROXY: str = "http://164.70.96.2:3128"


# ===== Rapras Configuration =====
# Base URL for Rapras website
RAPRAS_BASE_URL: str = "https://www.rapras.jp"

# Path to sum analyse page (seller aggregation)
RAPRAS_SUM_ANALYSE_PATH: str = "/sum_analyse"

# Minimum seller total price threshold (yen)
# Only sellers with total_price >= this value are collected
MIN_SELLER_PRICE: int = 100000


# ===== Retry Strategy Configuration =====
# Maximum number of retry attempts for failed requests
MAX_RETRY_ATTEMPTS: int = 3

# Exponential backoff intervals in seconds
# Pattern: (1s, 2s, 4s) for 1st, 2nd, 3rd retry
RETRY_BACKOFF_SECONDS: tuple[int, ...] = (1, 2, 4)


# ===== Parallel Processing Configuration =====
# Maximum number of concurrent seller processing tasks
MAX_CONCURRENT_SELLERS: int = 3

# Timeout warning threshold in seconds (5 minutes)
TIMEOUT_WARNING_SECONDS: int = 300
