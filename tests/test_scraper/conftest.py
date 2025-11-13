"""Shared fixtures for Yahoo scraper tests."""

import pytest

from modules.scraper.session_manager import SessionManager
from modules.scraper.yahoo_scraper import YahooAuctionScraper


@pytest.fixture
def temp_session_dir(tmp_path):
    """一時的なセッションディレクトリを作成"""
    return tmp_path / "test_sessions"


@pytest.fixture
def session_manager(temp_session_dir):
    """SessionManagerインスタンスを作成"""
    return SessionManager(session_dir=str(temp_session_dir))


@pytest.fixture
def proxy_config():
    """プロキシ設定を作成"""
    return {
        "url": "http://164.70.96.2:3128",
        "username": "test_proxy_user",
        "password": "test_proxy_pass",
    }


@pytest.fixture
def yahoo_scraper(session_manager, proxy_config):
    """YahooAuctionScraperインスタンスを作成"""
    return YahooAuctionScraper(session_manager=session_manager, proxy_config=proxy_config)
