"""
Test suite for modules.config.constants

Tests verify that all application constants are defined with correct values.
"""


class TestConstants:
    """Test constants.py module"""

    def test_max_products_per_seller_is_defined(self):
        """
        Given: constants module
        When: MAX_PRODUCTS_PER_SELLER is imported
        Then: it should equal 12
        """
        from modules.config.constants import MAX_PRODUCTS_PER_SELLER

        assert MAX_PRODUCTS_PER_SELLER == 12

    def test_min_seller_price_is_defined(self):
        """
        Given: constants module
        When: MIN_SELLER_PRICE is imported
        Then: it should equal 100000
        """
        from modules.config.constants import MIN_SELLER_PRICE

        assert MIN_SELLER_PRICE == 100000

    def test_max_retry_attempts_is_defined(self):
        """
        Given: constants module
        When: MAX_RETRY_ATTEMPTS is imported
        Then: it should equal 3
        """
        from modules.config.constants import MAX_RETRY_ATTEMPTS

        assert MAX_RETRY_ATTEMPTS == 3

    def test_yahoo_proxy_is_defined(self):
        """
        Given: constants module
        When: YAHOO_PROXY is imported
        Then: it should equal "http://164.70.96.2:3128"
        """
        from modules.config.constants import YAHOO_PROXY

        assert YAHOO_PROXY == "http://164.70.96.2:3128"

    def test_rapras_base_url_is_defined(self):
        """
        Given: constants module
        When: RAPRAS_BASE_URL is imported
        Then: it should equal "https://www.rapras.jp"
        """
        from modules.config.constants import RAPRAS_BASE_URL

        assert RAPRAS_BASE_URL == "https://www.rapras.jp"

    def test_rapras_sum_analyse_path_is_defined(self):
        """
        Given: constants module
        When: RAPRAS_SUM_ANALYSE_PATH is imported
        Then: it should equal "/sum_analyse"
        """
        from modules.config.constants import RAPRAS_SUM_ANALYSE_PATH

        assert RAPRAS_SUM_ANALYSE_PATH == "/sum_analyse"

    def test_retry_backoff_seconds_is_defined(self):
        """
        Given: constants module
        When: RETRY_BACKOFF_SECONDS is imported
        Then: it should equal (1, 2, 4)
        """
        from modules.config.constants import RETRY_BACKOFF_SECONDS

        assert RETRY_BACKOFF_SECONDS == (1, 2, 4)

    def test_constants_are_immutable_types(self):
        """
        Given: constants module
        When: checking constant types
        Then: all should be immutable (int, str, or tuple)
        """
        from modules.config.constants import (
            MAX_PRODUCTS_PER_SELLER,
            MAX_RETRY_ATTEMPTS,
            MIN_SELLER_PRICE,
            RAPRAS_BASE_URL,
            RAPRAS_SUM_ANALYSE_PATH,
            RETRY_BACKOFF_SECONDS,
            YAHOO_PROXY,
        )

        # Check immutable types
        assert isinstance(MAX_PRODUCTS_PER_SELLER, int)
        assert isinstance(MIN_SELLER_PRICE, int)
        assert isinstance(MAX_RETRY_ATTEMPTS, int)
        assert isinstance(YAHOO_PROXY, str)
        assert isinstance(RAPRAS_BASE_URL, str)
        assert isinstance(RAPRAS_SUM_ANALYSE_PATH, str)
        # RETRY_BACKOFF_SECONDS should be a tuple (immutable)
        assert isinstance(RETRY_BACKOFF_SECONDS, tuple)

    def test_retry_backoff_seconds_length(self):
        """
        Given: constants module
        When: RETRY_BACKOFF_SECONDS is imported
        Then: it should have exactly 3 elements
        """
        from modules.config.constants import RETRY_BACKOFF_SECONDS

        assert len(RETRY_BACKOFF_SECONDS) == 3

    def test_retry_backoff_seconds_exponential_pattern(self):
        """
        Given: constants module
        When: RETRY_BACKOFF_SECONDS is imported
        Then: it should follow exponential backoff pattern (1, 2, 4)
        """
        from modules.config.constants import RETRY_BACKOFF_SECONDS

        # Verify exponential backoff: each element doubles
        assert RETRY_BACKOFF_SECONDS[0] == 1
        assert RETRY_BACKOFF_SECONDS[1] == 2
        assert RETRY_BACKOFF_SECONDS[2] == 4

    def test_min_seller_price_boundary_value(self):
        """
        Given: constants module
        When: MIN_SELLER_PRICE is imported
        Then: it should be exactly 100000 (boundary value)
        """
        from modules.config.constants import MIN_SELLER_PRICE

        # Verify boundary value
        assert MIN_SELLER_PRICE == 100000
        assert MIN_SELLER_PRICE > 0

    def test_yahoo_proxy_url_format(self):
        """
        Given: constants module
        When: YAHOO_PROXY is imported
        Then: it should be a valid HTTP URL
        """
        from modules.config.constants import YAHOO_PROXY

        # Verify URL format
        assert YAHOO_PROXY.startswith("http://")
        assert ":" in YAHOO_PROXY  # Should contain port
        assert len(YAHOO_PROXY) > len("http://")

    def test_rapras_base_url_format(self):
        """
        Given: constants module
        When: RAPRAS_BASE_URL is imported
        Then: it should be a valid HTTPS URL
        """
        from modules.config.constants import RAPRAS_BASE_URL

        # Verify HTTPS URL format
        assert RAPRAS_BASE_URL.startswith("https://")
        assert len(RAPRAS_BASE_URL) > len("https://")

    def test_rapras_sum_analyse_path_format(self):
        """
        Given: constants module
        When: RAPRAS_SUM_ANALYSE_PATH is imported
        Then: it should start with /
        """
        from modules.config.constants import RAPRAS_SUM_ANALYSE_PATH

        # Verify path format
        assert RAPRAS_SUM_ANALYSE_PATH.startswith("/")

    def test_retry_backoff_seconds_immutability(self):
        """
        Given: RETRY_BACKOFF_SECONDS constant
        When: attempting to modify the constant
        Then: TypeError should be raised (tuple is immutable)
        """
        import pytest

        from modules.config.constants import RETRY_BACKOFF_SECONDS

        with pytest.raises(TypeError):
            RETRY_BACKOFF_SECONDS[0] = 10  # type: ignore

    def test_max_products_boundary_positive(self):
        """
        Given: constants module
        When: MAX_PRODUCTS_PER_SELLER is checked
        Then: it should be positive (greater than zero)
        """
        from modules.config.constants import MAX_PRODUCTS_PER_SELLER

        assert MAX_PRODUCTS_PER_SELLER > 0

    def test_max_retry_attempts_boundary_positive(self):
        """
        Given: constants module
        When: MAX_RETRY_ATTEMPTS is checked
        Then: it should be positive (greater than zero)
        """
        from modules.config.constants import MAX_RETRY_ATTEMPTS

        assert MAX_RETRY_ATTEMPTS > 0

    def test_min_seller_price_boundary_positive(self):
        """
        Given: constants module
        When: MIN_SELLER_PRICE is checked
        Then: it should be positive (greater than zero)
        """
        from modules.config.constants import MIN_SELLER_PRICE

        assert MIN_SELLER_PRICE > 0

    def test_retry_backoff_seconds_all_positive(self):
        """
        Given: constants module
        When: RETRY_BACKOFF_SECONDS is checked
        Then: all values should be positive
        """
        from modules.config.constants import RETRY_BACKOFF_SECONDS

        assert all(value > 0 for value in RETRY_BACKOFF_SECONDS)
