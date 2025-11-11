"""Data models for Yahoo Auction Seller Data Collection Analysis.

This module defines type-safe dataclass models following requirements 2 and 3
from .spec-workflow/specs/seller-data-collection-analysis/requirements.md.

Requirements:
- Requirement 2 (Yahoo Auctionsセラーページからの商品名取得)
- Requirement 3 (中間CSVエクスポート)
"""

from dataclasses import dataclass


@dataclass
class Seller:
    """Seller data model.

    Attributes:
        seller_name: セラー名（例: "アート工房 クリスプ"）
        seller_url: Yahoo AuctionsセラーページURL
        total_price: Rapras落札価格合計（円）
        product_titles: 商品名リスト（最大12件）
        is_anime_seller: 二次創作セラーフラグ（True/False/None=未判定）
    """

    seller_name: str
    seller_url: str
    total_price: int
    product_titles: list[str]
    is_anime_seller: bool | None = None


@dataclass
class Product:
    """Product data model.

    Attributes:
        title: 商品名（例: "らんまちゃん らんま A4 ポスター 同人 アニメ イラスト 美女 E017621"）
        seller_name: セラー名
    """

    title: str
    seller_name: str
