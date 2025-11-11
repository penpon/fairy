"""Test models.py - Seller and Product dataclasses unit tests.

Requirements:
- Requirement 2 (Yahoo Auctionsセラーページからの商品名取得)
- Requirement 3 (中間CSVエクスポート)
- Non-Functional Requirements (Testability - 95% coverage)
"""

import pytest

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
