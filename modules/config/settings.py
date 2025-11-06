"""Configuration management module for environment variables."""

import os
from dataclasses import dataclass


@dataclass
class RaprasConfig:
    """Rapras認証設定"""

    username: str
    password: str


@dataclass
class YahooConfig:
    """Yahoo Auctions認証設定"""

    phone_number: str


@dataclass
class ProxyConfig:
    """プロキシサーバー設定"""

    url: str
    username: str
    password: str


def load_rapras_config() -> RaprasConfig:
    """Rapras認証情報を環境変数から読み込み

    Returns:
        RaprasConfig: Rapras認証設定

    Raises:
        ValueError: 必須環境変数が設定されていない場合
    """
    username = os.getenv("RAPRAS_USERNAME")
    password = os.getenv("RAPRAS_PASSWORD")

    if not username:
        raise ValueError(
            "RAPRAS_USERNAME environment variable is not set. " "Please set it in your .env file."
        )

    if not password:
        raise ValueError(
            "RAPRAS_PASSWORD environment variable is not set. " "Please set it in your .env file."
        )

    return RaprasConfig(username=username, password=password)


def load_yahoo_config() -> YahooConfig:
    """Yahoo認証情報を環境変数から読み込み

    Returns:
        YahooConfig: Yahoo認証設定

    Raises:
        ValueError: 必須環境変数が設定されていない場合
    """
    phone_number = os.getenv("YAHOO_PHONE_NUMBER")

    if not phone_number:
        raise ValueError(
            "YAHOO_PHONE_NUMBER environment variable is not set. "
            "Please set it in your .env file."
        )

    return YahooConfig(phone_number=phone_number)


def load_proxy_config() -> ProxyConfig:
    """プロキシ設定を環境変数から読み込み

    Returns:
        ProxyConfig: プロキシ設定

    Raises:
        ValueError: 必須環境変数が設定されていない場合
    """
    url = os.getenv("PROXY_URL")
    username = os.getenv("PROXY_USERNAME")
    password = os.getenv("PROXY_PASSWORD")

    if not url:
        raise ValueError(
            "PROXY_URL environment variable is not set. " "Please set it in your .env file."
        )

    if not username:
        raise ValueError(
            "PROXY_USERNAME environment variable is not set. " "Please set it in your .env file."
        )

    if not password:
        raise ValueError(
            "PROXY_PASSWORD environment variable is not set. " "Please set it in your .env file."
        )

    return ProxyConfig(url=url, username=username, password=password)
