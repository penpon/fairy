"""Tests for AnimeFilter class.

This module tests the anime title detection functionality using Gemini CLI.
"""

import subprocess
from unittest.mock import MagicMock

import pytest

from modules.analyzer.anime_filter import AnimeFilter


class TestAnimeFilterInit:
    """Tests for AnimeFilter.__init__()"""

    def test_init_with_default_model(self):
        """Test initialization with default model."""
        # Given: No model parameter provided
        # When: AnimeFilter is instantiated
        filter_instance = AnimeFilter()
        # Then: Model should be "gemini-2.5-flash"
        assert filter_instance.model == "gemini-2.5-flash"

    def test_init_with_custom_model(self):
        """Test initialization with custom model."""
        # Given: Custom model parameter
        custom_model = "gemini-pro"
        # When: AnimeFilter is instantiated with custom model
        filter_instance = AnimeFilter(model=custom_model)
        # Then: Model should be the custom model
        assert filter_instance.model == custom_model


class TestIsAnimeTitle:
    """Tests for AnimeFilter.is_anime_title()"""

    def test_is_anime_title_returns_true_for_hai_response(self, mocker):
        """Test is_anime_title returns True when Gemini responds with 'はい'."""
        # Given: Gemini CLI returns "はい、これはアニメ作品です"
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(
            stdout="はい、これはアニメ作品です",
            stderr="",
            returncode=0,
        )
        filter_instance = AnimeFilter()
        title = "らんまちゃん らんま"

        # When: is_anime_title is called
        result = filter_instance.is_anime_title(title)

        # Then: Result should be True
        assert result is True
        mock_run.assert_called_once()

    def test_is_anime_title_returns_true_for_anime_keyword(self, mocker):
        """Test is_anime_title returns True when Gemini responds with 'アニメ' keyword."""
        # Given: Gemini CLI returns "これはアニメ作品です"
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(
            stdout="これはアニメ作品です",
            stderr="",
            returncode=0,
        )
        filter_instance = AnimeFilter()
        title = "エヴァンゲリオン"

        # When: is_anime_title is called
        result = filter_instance.is_anime_title(title)

        # Then: Result should be True
        assert result is True

    def test_is_anime_title_returns_false_for_iie_response(self, mocker):
        """Test is_anime_title returns False when Gemini responds with 'いいえ'."""
        # Given: Gemini CLI returns "いいえ、アニメ作品ではありません"
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(
            stdout="いいえ、アニメ作品ではありません",
            stderr="",
            returncode=0,
        )
        filter_instance = AnimeFilter()
        title = "iPhone ケース"

        # When: is_anime_title is called
        result = filter_instance.is_anime_title(title)

        # Then: Result should be False
        assert result is False

    def test_is_anime_title_extracts_first_two_words(self, mocker):
        """Test that only first 2 words are extracted from product title."""
        # Given: Product title with multiple words
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(
            stdout="はい",
            stderr="",
            returncode=0,
        )
        filter_instance = AnimeFilter()
        product_title = "らんまちゃん らんま A4 ポスター 同人 アニメ イラスト 美女 E017621"

        # When: is_anime_title is called
        result = filter_instance.is_anime_title(product_title)

        # Then: Gemini CLI should be called with only first 2 words
        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "らんまちゃん らんま" in " ".join(call_args)
        # Ensure "A4 ポスター" is NOT in the prompt
        assert "A4" not in " ".join(call_args) or "ポスター" not in " ".join(call_args)

    def test_is_anime_title_handles_gemini_api_error(self, mocker):
        """Test is_anime_title handles GeminiAPIError gracefully."""
        # Given: Gemini CLI returns error
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "gemini", stderr="API rate limit exceeded"
        )
        filter_instance = AnimeFilter()
        title = "テストタイトル"

        # When: is_anime_title is called
        # Then: Should raise GeminiAPIError
        with pytest.raises(Exception) as exc_info:
            filter_instance.is_anime_title(title)
        assert "GeminiAPIError" in str(
            type(exc_info.value).__name__
        ) or "CalledProcessError" in str(type(exc_info.value).__name__)

    def test_is_anime_title_with_empty_title(self, mocker):
        """Test is_anime_title with empty title."""
        # Given: Empty title string
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(
            stdout="いいえ",
            stderr="",
            returncode=0,
        )
        filter_instance = AnimeFilter()
        title = ""

        # When: is_anime_title is called
        result = filter_instance.is_anime_title(title)

        # Then: Should handle gracefully and return False
        assert result is False

    def test_is_anime_title_with_single_word(self, mocker):
        """Test is_anime_title with single word title (boundary case)."""
        # Given: Title with only 1 word
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(
            stdout="はい",
            stderr="",
            returncode=0,
        )
        filter_instance = AnimeFilter()
        title = "らんま"

        # When: is_anime_title is called
        result = filter_instance.is_anime_title(title)

        # Then: Should work with 1 word
        assert result is True


class TestFilterSellers:
    """Tests for AnimeFilter.filter_sellers()"""

    def test_filter_sellers_with_early_termination(self, mocker):
        """Test filter_sellers implements early termination after first 'はい'."""
        # Given: Seller with 3 products, first product is anime
        mock_run = mocker.patch("subprocess.run")
        # First call returns "はい", subsequent calls should not happen
        mock_run.return_value = MagicMock(
            stdout="はい、これはアニメ作品です",
            stderr="",
            returncode=0,
        )
        filter_instance = AnimeFilter()
        sellers = [
            {
                "seller_name": "テストセラー",
                "seller_url": "https://example.com/seller1",
                "product_titles": [
                    "らんまちゃん らんま A4 ポスター",
                    "エヴァンゲリオン グッズ",
                    "ナルト フィギュア",
                ],
            }
        ]

        # When: filter_sellers is called
        result = filter_instance.filter_sellers(sellers)

        # Then: Should mark seller as anime seller and call Gemini CLI only once
        assert len(result) == 1
        assert result[0]["is_anime_seller"] is True
        assert mock_run.call_count == 1  # Only first product checked

    def test_filter_sellers_with_all_false(self, mocker):
        """Test filter_sellers when all products are non-anime."""
        # Given: Seller with 3 products, all non-anime
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(
            stdout="いいえ、アニメ作品ではありません",
            stderr="",
            returncode=0,
        )
        filter_instance = AnimeFilter()
        sellers = [
            {
                "seller_name": "テストセラー",
                "seller_url": "https://example.com/seller1",
                "product_titles": [
                    "iPhone ケース 新品",
                    "腕時計 メンズ",
                    "バッグ レディース",
                ],
            }
        ]

        # When: filter_sellers is called
        result = filter_instance.filter_sellers(sellers)

        # Then: Should mark seller as non-anime seller and check all products
        assert len(result) == 1
        assert result[0]["is_anime_seller"] is False
        assert mock_run.call_count == 3  # All 3 products checked

    def test_filter_sellers_handles_gemini_error_gracefully(self, mocker):
        """Test filter_sellers continues to next product on GeminiAPIError."""
        # Given: Seller with 3 products, first product causes error
        mock_run = mocker.patch("subprocess.run")
        # First call fails, second and third succeed
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "gemini", stderr="API error"),
            MagicMock(stdout="いいえ", stderr="", returncode=0),
            MagicMock(stdout="はい", stderr="", returncode=0),
        ]
        filter_instance = AnimeFilter()
        sellers = [
            {
                "seller_name": "テストセラー",
                "seller_url": "https://example.com/seller1",
                "product_titles": [
                    "エラー商品",
                    "普通の商品",
                    "アニメ商品",
                ],
            }
        ]

        # When: filter_sellers is called
        result = filter_instance.filter_sellers(sellers)

        # Then: Should skip error product and continue, finding anime on 3rd product
        assert len(result) == 1
        assert result[0]["is_anime_seller"] is True
        assert mock_run.call_count == 3

    def test_filter_sellers_with_empty_product_titles(self, mocker):
        """Test filter_sellers with seller having no products."""
        # Given: Seller with empty product_titles
        mock_run = mocker.patch("subprocess.run")
        filter_instance = AnimeFilter()
        sellers = [
            {
                "seller_name": "空のセラー",
                "seller_url": "https://example.com/seller1",
                "product_titles": [],
            }
        ]

        # When: filter_sellers is called
        result = filter_instance.filter_sellers(sellers)

        # Then: Should mark as False (no anime products found)
        assert len(result) == 1
        assert result[0]["is_anime_seller"] is False
        assert mock_run.call_count == 0  # No Gemini calls

    def test_filter_sellers_with_multiple_sellers(self, mocker):
        """Test filter_sellers with multiple sellers."""
        # Given: 2 sellers, first is anime, second is not
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = [
            MagicMock(stdout="はい", stderr="", returncode=0),  # Seller 1, product 1
            MagicMock(stdout="いいえ", stderr="", returncode=0),  # Seller 2, product 1
            MagicMock(stdout="いいえ", stderr="", returncode=0),  # Seller 2, product 2
        ]
        filter_instance = AnimeFilter()
        sellers = [
            {
                "seller_name": "アニメセラー",
                "seller_url": "https://example.com/seller1",
                "product_titles": ["らんま グッズ"],
            },
            {
                "seller_name": "普通のセラー",
                "seller_url": "https://example.com/seller2",
                "product_titles": ["iPhone ケース", "バッグ"],
            },
        ]

        # When: filter_sellers is called
        result = filter_instance.filter_sellers(sellers)

        # Then: First seller is anime, second is not
        assert len(result) == 2
        assert result[0]["is_anime_seller"] is True
        assert result[1]["is_anime_seller"] is False
