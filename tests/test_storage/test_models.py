"""Test models.py - Seller and Product dataclasses unit tests.

Requirements:
- Requirement 2 (Yahoo Auctionsセラーページからの商品名取得)
- Requirement 3 (中間CSVエクスポート)
- Non-Functional Requirements (Testability - 90% coverage)
"""

from modules.storage.models import Product, Seller


class TestSellerModel:
    """Test Seller dataclass."""

    def test_seller_instantiation_normal(self):
        """T001: 正常系 - 全フィールドが正しく設定されたSellerインスタンス作成."""
        # Given: 有効なデータ
        # When: Sellerインスタンスを作成
        seller = Seller(
            seller_name="アート工房 クリスプ",
            seller_url="https://auctions.yahoo.co.jp/sellinglist/56qo7eumP8EYVhY6kWg5poNgj3Wef",
            total_price=150000,
            product_titles=["商品1", "商品2"],
            is_anime_seller=None,
        )

        # Then: 全フィールドが正しく設定される
        assert seller.seller_name == "アート工房 クリスプ"
        assert (
            seller.seller_url
            == "https://auctions.yahoo.co.jp/sellinglist/56qo7eumP8EYVhY6kWg5poNgj3Wef"
        )
        assert seller.total_price == 150000
        assert seller.product_titles == ["商品1", "商品2"]
        assert seller.is_anime_seller is None

    def test_seller_is_anime_seller_true(self):
        """T002: 正常系 - is_anime_seller=Trueの二次創作セラー."""
        # Given: アニメ判定がTrueのデータ
        # When: Sellerインスタンスを作成
        seller = Seller(
            seller_name="セラーA",
            seller_url="https://example.com/sellerA",
            total_price=200000,
            product_titles=["らんまちゃん らんま"],
            is_anime_seller=True,
        )

        # Then: is_anime_sellerがTrueになる
        assert seller.is_anime_seller is True

    def test_seller_is_anime_seller_false(self):
        """T003: 正常系 - is_anime_seller=Falseの非二次創作セラー."""
        # Given: アニメ判定がFalseのデータ
        # When: Sellerインスタンスを作成
        seller = Seller(
            seller_name="セラーB",
            seller_url="https://example.com/sellerB",
            total_price=100000,
            product_titles=["iPhone ケース"],
            is_anime_seller=False,
        )

        # Then: is_anime_sellerがFalseになる
        assert seller.is_anime_seller is False

    def test_seller_empty_product_titles(self):
        """T004: 境界値 - product_titlesが空リスト."""
        # Given: product_titlesが空のデータ
        # When: Sellerインスタンスを作成
        seller = Seller(
            seller_name="セラーC",
            seller_url="https://example.com/sellerC",
            total_price=100000,
            product_titles=[],
        )

        # Then: product_titlesが空リストになる
        assert seller.product_titles == []

    def test_seller_total_price_boundary_minimum(self):
        """T005: 境界値 - total_priceが最小値(10万円)."""
        # Given: total_priceが10万円のデータ
        # When: Sellerインスタンスを作成
        seller = Seller(
            seller_name="セラーD",
            seller_url="https://example.com/sellerD",
            total_price=100000,
            product_titles=["商品1"],
        )

        # Then: total_priceが10万円になる
        assert seller.total_price == 100000


class TestProductModel:
    """Test Product dataclass."""

    def test_product_instantiation_normal(self):
        """T006: 正常系 - 全フィールドが正しく設定されたProductインスタンス作成."""
        # Given: 有効なデータ
        # When: Productインスタンスを作成
        product = Product(
            title="らんまちゃん らんま A4 ポスター 同人 アニメ イラスト 美女 E017621",
            seller_name="アート工房 クリスプ",
        )

        # Then: 全フィールドが正しく設定される
        assert product.title == "らんまちゃん らんま A4 ポスター 同人 アニメ イラスト 美女 E017621"
        assert product.seller_name == "アート工房 クリスプ"

    def test_product_empty_title(self):
        """T007: 境界値 - titleが空文字列."""
        # Given: titleが空文字列のデータ
        # When: Productインスタンスを作成
        product = Product(
            title="",
            seller_name="セラーE",
        )

        # Then: titleが空文字列になる
        assert product.title == ""

    def test_product_empty_seller_name(self):
        """T008: 境界値 - seller_nameが空文字列."""
        # Given: seller_nameが空文字列のデータ
        # When: Productインスタンスを作成
        product = Product(
            title="商品タイトル",
            seller_name="",
        )

        # Then: seller_nameが空文字列になる
        assert product.seller_name == ""


class TestSellerModelErrorCases:
    """Test Seller dataclass error cases."""

    def test_seller_none_seller_name(self):
        """T009: 異常系 - seller_nameがNone."""
        # Given: seller_nameがNoneのデータ
        # When: Sellerインスタンスを作成
        seller = Seller(
            seller_name=None,
            seller_url="https://example.com",
            total_price=100000,
            product_titles=[],
        )

        # Then: seller_nameがNoneで作成される（型安全性違反）
        assert seller.seller_name is None

    def test_seller_none_seller_url(self):
        """T010: 異常系 - seller_urlがNone."""
        # Given: seller_urlがNoneのデータ
        # When: Sellerインスタンスを作成
        seller = Seller(
            seller_name="テストセラー",
            seller_url=None,
            total_price=100000,
            product_titles=[],
        )

        # Then: seller_urlがNoneで作成される（型安全性違反）
        assert seller.seller_url is None

    def test_seller_none_product_titles(self):
        """T011: 異常系 - product_titlesがNone."""
        # Given: product_titlesがNoneのデータ
        # When: Sellerインスタンスを作成
        seller = Seller(
            seller_name="テストセラー",
            seller_url="https://example.com",
            total_price=100000,
            product_titles=None,
        )

        # Then: product_titlesがNoneで作成される（型安全性違反）
        assert seller.product_titles is None

    def test_seller_invalid_total_price_type(self):
        """T012: 異常系 - total_priceが文字列."""
        # Given: total_priceが文字列のデータ
        # When: Sellerインスタンスを作成
        seller = Seller(
            seller_name="テストセラー",
            seller_url="https://example.com",
            total_price="invalid",
            product_titles=[],
        )

        # Then: total_priceが文字列で作成される（型安全性違反）
        assert seller.total_price == "invalid"

    def test_seller_negative_total_price(self):
        """T013: 異常系 - total_priceが負の値."""
        # Given: total_priceが負の値のデータ
        # When: Sellerインスタンスを作成
        seller = Seller(
            seller_name="テストセラー",
            seller_url="https://example.com",
            total_price=-1000,
            product_titles=[],
        )

        # Then: total_priceが負の値で作成される（ビジネスロジック違反）
        assert seller.total_price == -1000

    def test_seller_invalid_is_anime_seller_type(self):
        """T014: 異常系 - is_anime_sellerが文字列."""
        # Given: is_anime_sellerが文字列のデータ
        # When: Sellerインスタンスを作成
        seller = Seller(
            seller_name="テストセラー",
            seller_url="https://example.com",
            total_price=100000,
            product_titles=[],
            is_anime_seller="invalid",
        )

        # Then: is_anime_sellerが文字列で作成される（型安全性違反）
        assert seller.is_anime_seller == "invalid"


class TestProductModelErrorCases:
    """Test Product dataclass error cases."""

    def test_product_none_title(self):
        """T015: 異常系 - titleがNone."""
        # Given: titleがNoneのデータ
        # When: Productインスタンスを作成
        product = Product(
            title=None,
            seller_name="テストセラー",
        )

        # Then: titleがNoneで作成される（型安全性違反）
        assert product.title is None

    def test_product_none_seller_name(self):
        """T016: 異常系 - seller_nameがNone."""
        # Given: seller_nameがNoneのデータ
        # When: Productインスタンスを作成
        product = Product(
            title="テスト商品",
            seller_name=None,
        )

        # Then: seller_nameがNoneで作成される（型安全性違反）
        assert product.seller_name is None

    def test_product_invalid_title_type(self):
        """T017: 異常系 - titleが数値."""
        # Given: titleが数値のデータ
        # When: Productインスタンスを作成
        product = Product(
            title=12345,
            seller_name="テストセラー",
        )

        # Then: titleが数値で作成される（型安全性違反）
        assert product.title == 12345

    def test_product_invalid_seller_name_type(self):
        """T018: 異常系 - seller_nameがリスト."""
        # Given: seller_nameがリストのデータ
        # When: Productインスタンスを作成
        product = Product(
            title="テスト商品",
            seller_name=["セラーA", "セラーB"],
        )

        # Then: seller_nameがリストで作成される（型安全性違反）
        assert product.seller_name == ["セラーA", "セラーB"]
