"""Pytest configuration and fixtures."""

from pathlib import Path

from dotenv import load_dotenv


def pytest_configure(config):
    """Load .env file before running tests."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
