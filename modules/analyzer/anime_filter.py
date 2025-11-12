"""Anime title detection module using Gemini CLI.

This module provides AnimeFilter class to identify anime-related products
using Gemini CLI via subprocess.
"""

import subprocess
from typing import Any

from modules.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiAPIError(Exception):
    """Exception raised when Gemini CLI execution fails."""

    pass


class AnimeFilter:
    """Filter for detecting anime titles using Gemini CLI.

    Attributes:
        model (str): Gemini model name to use for title detection.
    """

    def __init__(self, model: str = "gemini-2.5-flash") -> None:
        """Initialize AnimeFilter.

        Args:
            model: Gemini CLI model name (default: "gemini-2.5-flash").
        """
        self.model = model
        logger.info(f"AnimeFilter initialized with model: {model}")

    def _extract_title_words(self, title: str, max_words: int = 2) -> str:
        """Extract first N words from title.

        Args:
            title: Full product title.
            max_words: Maximum number of words to extract.

        Returns:
            str: Extracted title (first N words joined by space).
        """
        words = title.split()
        return " ".join(words[:max_words])

    def _parse_gemini_response(self, response: str) -> bool:
        """Parse Gemini CLI response to determine if title is anime.

        Args:
            response: Gemini CLI stdout response.

        Returns:
            bool: True if response indicates anime title, False otherwise.
        """
        # Check for negative indicators
        has_negative = any(neg in response for neg in ["いいえ", "ではありません", "ではない"])
        # Check for positive indicators
        has_positive = "はい" in response

        # Positive response takes precedence
        if has_positive and not has_negative:
            return True
        # "アニメ" keyword in non-negative context
        if "アニメ" in response and not has_negative:
            return True

        return False

    def is_anime_title(self, title: str) -> bool:
        """Check if a title is an anime title using Gemini CLI.

        Args:
            title: Product title (first 2 words will be extracted).

        Returns:
            bool: True if title is anime, False otherwise.

        Raises:
            GeminiAPIError: If Gemini CLI execution fails.
        """
        # Extract first 2 words from title
        extracted_title = self._extract_title_words(title)

        # Handle empty title
        if not extracted_title.strip():
            logger.warning("Empty title provided, returning False")
            return False

        # Construct Gemini CLI prompt
        prompt = f"このタイトルはアニメ作品ですか?(タイトル: {extracted_title})"

        try:
            # Execute Gemini CLI
            result = subprocess.run(
                ["gemini", "-m", self.model, "-p", prompt],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,  # 30 second timeout
            )

            response = result.stdout.strip()
            logger.info(f"Gemini response for '{extracted_title}': {response[:50]}...")

            # Parse response
            return self._parse_gemini_response(response)

        except subprocess.CalledProcessError as e:
            logger.error(f"Gemini CLI execution failed for '{extracted_title}': {e.stderr}")
            raise GeminiAPIError(f"Gemini CLI execution failed: {e.stderr}") from e
        except subprocess.TimeoutExpired:
            logger.error(f"Gemini CLI timeout for '{extracted_title}'")
            raise GeminiAPIError(f"Gemini CLI timeout after 30 seconds")

    def filter_sellers(self, sellers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter sellers and mark anime sellers.

        Implements early termination: stops checking products after first "はい" response.

        Args:
            sellers: List of seller dictionaries with keys:
                - seller_name (str): Seller name
                - seller_url (str): Seller page URL
                - product_titles (list[str]): List of product titles

        Returns:
            list[dict]: List of seller dictionaries with added key:
                - is_anime_seller (bool): True if seller has anime products
        """
        result = []

        for seller in sellers:
            seller_name = seller.get("seller_name", "Unknown")
            product_titles = seller.get("product_titles", [])

            logger.info(f"Processing seller: {seller_name} ({len(product_titles)} products)")

            # Default to False
            is_anime_seller = False

            # Early termination: stop after first "はい"
            for idx, product_title in enumerate(product_titles):
                try:
                    if self.is_anime_title(product_title):
                        logger.info(
                            f"Anime detected for seller {seller_name} at product {idx + 1}: {product_title[:30]}..."
                        )
                        is_anime_seller = True
                        break  # Early termination
                except GeminiAPIError as e:
                    logger.warning(
                        f"Failed to check product '{product_title[:30]}...' for seller {seller_name}: {e}. Continuing to next product."
                    )
                    # Continue to next product on error

            result.append(
                {
                    "seller_name": seller_name,
                    "seller_url": seller.get("seller_url", ""),
                    "is_anime_seller": is_anime_seller,
                }
            )

            logger.info(
                f"Seller {seller_name} marked as {'anime' if is_anime_seller else 'non-anime'} seller"
            )

        return result
