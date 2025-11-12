"""Configuration management module for environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

__all__ = [
    "RaprasConfig",
    "YahooConfig",
    "ProxyConfig",
    "load_dotenv_file",
    "load_rapras_config",
    "load_yahoo_config",
    "load_proxy_config",
]


def load_dotenv_file(dotenv_path: str | None = None) -> bool:
    """.envファイルを読み込む

    Args:
        dotenv_path: .envファイルのパス（省略時は".env"）

    Returns:
        bool: 読み込み成功時True

    Raises:
        FileNotFoundError: .envファイルが存在しない場合
    """
    if dotenv_path is None:
        dotenv_path = ".env"

    env_file = Path(dotenv_path)
    if not env_file.exists():
        raise FileNotFoundError(
            f".env file not found at: {env_file.absolute()}. "
            "Please create .env file based on .env.example"
        )

    # override=Falseで環境変数が優先される
    success = load_dotenv(dotenv_path=dotenv_path, override=False)
    if not success:
        raise ValueError(
            f"Failed to load .env file at: {env_file.absolute()}. "
            "Please check the file format."
        )
    return True


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
            "RAPRAS_USERNAME environment variable is not set. Please set it in your .env file."
        )

    if not password:
        raise ValueError(
            "RAPRAS_PASSWORD environment variable is not set. Please set it in your .env file."
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
            "YAHOO_PHONE_NUMBER environment variable is not set. Please set it in your .env file."
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
            "PROXY_URL environment variable is not set. Please set it in your .env file."
        )

    if not username:
        raise ValueError(
            "PROXY_USERNAME environment variable is not set. Please set it in your .env file."
        )

    if not password:
        raise ValueError(
            "PROXY_PASSWORD environment variable is not set. Please set it in your .env file."
        )

    return ProxyConfig(url=url, username=username, password=password)
