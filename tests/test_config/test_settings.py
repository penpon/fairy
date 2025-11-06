"""Unit tests for Settings configuration management."""

import pytest

from modules.config.settings import (
    ProxyConfig,
    RaprasConfig,
    YahooConfig,
    load_proxy_config,
    load_rapras_config,
    load_yahoo_config,
)


class TestRaprasConfig:
    """RaprasConfigのテストクラス"""

    def test_load_rapras_config_success(self, monkeypatch):
        """正常系: Rapras設定が正常に読み込まれることを確認"""
        # Given: 環境変数が設定されている
        monkeypatch.setenv("RAPRAS_USERNAME", "test_user")
        monkeypatch.setenv("RAPRAS_PASSWORD", "test_password")

        # When: 設定を読み込み
        config = load_rapras_config()

        # Then: 正しい設定が返される
        assert isinstance(config, RaprasConfig)
        assert config.username == "test_user"
        assert config.password == "test_password"

    def test_load_rapras_config_missing_username(self, monkeypatch):
        """異常系: RAPRAS_USERNAMEが未設定の場合に例外が発生することを確認"""
        # Given: パスワードのみ設定されている
        monkeypatch.delenv("RAPRAS_USERNAME", raising=False)
        monkeypatch.setenv("RAPRAS_PASSWORD", "test_password")

        # When/Then: ValueErrorが発生する
        with pytest.raises(ValueError) as exc_info:
            load_rapras_config()

        # Then: エラーメッセージが適切
        assert "RAPRAS_USERNAME" in str(exc_info.value)
        assert "not set" in str(exc_info.value)

    def test_load_rapras_config_missing_password(self, monkeypatch):
        """異常系: RAPRAS_PASSWORDが未設定の場合に例外が発生することを確認"""
        # Given: ユーザー名のみ設定されている
        monkeypatch.setenv("RAPRAS_USERNAME", "test_user")
        monkeypatch.delenv("RAPRAS_PASSWORD", raising=False)

        # When/Then: ValueErrorが発生する
        with pytest.raises(ValueError) as exc_info:
            load_rapras_config()

        # Then: エラーメッセージが適切
        assert "RAPRAS_PASSWORD" in str(exc_info.value)
        assert "not set" in str(exc_info.value)

    def test_load_rapras_config_missing_all(self, monkeypatch):
        """異常系: 全ての環境変数が未設定の場合に例外が発生することを確認"""
        # Given: 環境変数が未設定
        monkeypatch.delenv("RAPRAS_USERNAME", raising=False)
        monkeypatch.delenv("RAPRAS_PASSWORD", raising=False)

        # When/Then: ValueErrorが発生する
        with pytest.raises(ValueError) as exc_info:
            load_rapras_config()

        # Then: エラーメッセージが適切
        assert "RAPRAS_USERNAME" in str(exc_info.value)

    def test_rapras_config_dataclass(self):
        """正常系: RaprasConfigデータクラスが正しく動作することを確認"""
        # Given/When: データクラスを直接作成
        config = RaprasConfig(username="test_user", password="test_pass")

        # Then: 属性が正しく設定される
        assert config.username == "test_user"
        assert config.password == "test_pass"


class TestYahooConfig:
    """YahooConfigのテストクラス"""

    def test_load_yahoo_config_success(self, monkeypatch):
        """正常系: Yahoo設定が正常に読み込まれることを確認"""
        # Given: 環境変数が設定されている
        monkeypatch.setenv("YAHOO_PHONE_NUMBER", "09012345678")

        # When: 設定を読み込み
        config = load_yahoo_config()

        # Then: 正しい設定が返される
        assert isinstance(config, YahooConfig)
        assert config.phone_number == "09012345678"

    def test_load_yahoo_config_missing_phone_number(self, monkeypatch):
        """異常系: YAHOO_PHONE_NUMBERが未設定の場合に例外が発生することを確認"""
        # Given: 環境変数が未設定
        monkeypatch.delenv("YAHOO_PHONE_NUMBER", raising=False)

        # When/Then: ValueErrorが発生する
        with pytest.raises(ValueError) as exc_info:
            load_yahoo_config()

        # Then: エラーメッセージが適切
        assert "YAHOO_PHONE_NUMBER" in str(exc_info.value)
        assert "not set" in str(exc_info.value)

    def test_yahoo_config_dataclass(self):
        """正常系: YahooConfigデータクラスが正しく動作することを確認"""
        # Given/When: データクラスを直接作成
        config = YahooConfig(phone_number="09012345678")

        # Then: 属性が正しく設定される
        assert config.phone_number == "09012345678"


class TestProxyConfig:
    """ProxyConfigのテストクラス"""

    def test_load_proxy_config_success(self, monkeypatch):
        """正常系: プロキシ設定が正常に読み込まれることを確認"""
        # Given: 環境変数が設定されている
        monkeypatch.setenv("PROXY_URL", "http://proxy.example.com:3128")
        monkeypatch.setenv("PROXY_USERNAME", "proxy_user")
        monkeypatch.setenv("PROXY_PASSWORD", "proxy_pass")

        # When: 設定を読み込み
        config = load_proxy_config()

        # Then: 正しい設定が返される
        assert isinstance(config, ProxyConfig)
        assert config.url == "http://proxy.example.com:3128"
        assert config.username == "proxy_user"
        assert config.password == "proxy_pass"

    def test_load_proxy_config_missing_url(self, monkeypatch):
        """異常系: PROXY_URLが未設定の場合に例外が発生することを確認"""
        # Given: URL以外の環境変数が設定されている
        monkeypatch.delenv("PROXY_URL", raising=False)
        monkeypatch.setenv("PROXY_USERNAME", "proxy_user")
        monkeypatch.setenv("PROXY_PASSWORD", "proxy_pass")

        # When/Then: ValueErrorが発生する
        with pytest.raises(ValueError) as exc_info:
            load_proxy_config()

        # Then: エラーメッセージが適切
        assert "PROXY_URL" in str(exc_info.value)
        assert "not set" in str(exc_info.value)

    def test_load_proxy_config_missing_username(self, monkeypatch):
        """異常系: PROXY_USERNAMEが未設定の場合に例外が発生することを確認"""
        # Given: ユーザー名以外の環境変数が設定されている
        monkeypatch.setenv("PROXY_URL", "http://proxy.example.com:3128")
        monkeypatch.delenv("PROXY_USERNAME", raising=False)
        monkeypatch.setenv("PROXY_PASSWORD", "proxy_pass")

        # When/Then: ValueErrorが発生する
        with pytest.raises(ValueError) as exc_info:
            load_proxy_config()

        # Then: エラーメッセージが適切
        assert "PROXY_USERNAME" in str(exc_info.value)
        assert "not set" in str(exc_info.value)

    def test_load_proxy_config_missing_password(self, monkeypatch):
        """異常系: PROXY_PASSWORDが未設定の場合に例外が発生することを確認"""
        # Given: パスワード以外の環境変数が設定されている
        monkeypatch.setenv("PROXY_URL", "http://proxy.example.com:3128")
        monkeypatch.setenv("PROXY_USERNAME", "proxy_user")
        monkeypatch.delenv("PROXY_PASSWORD", raising=False)

        # When/Then: ValueErrorが発生する
        with pytest.raises(ValueError) as exc_info:
            load_proxy_config()

        # Then: エラーメッセージが適切
        assert "PROXY_PASSWORD" in str(exc_info.value)
        assert "not set" in str(exc_info.value)

    def test_load_proxy_config_missing_all(self, monkeypatch):
        """異常系: 全ての環境変数が未設定の場合に例外が発生することを確認"""
        # Given: 環境変数が未設定
        monkeypatch.delenv("PROXY_URL", raising=False)
        monkeypatch.delenv("PROXY_USERNAME", raising=False)
        monkeypatch.delenv("PROXY_PASSWORD", raising=False)

        # When/Then: ValueErrorが発生する
        with pytest.raises(ValueError) as exc_info:
            load_proxy_config()

        # Then: エラーメッセージが適切
        assert "PROXY_URL" in str(exc_info.value)

    def test_proxy_config_dataclass(self):
        """正常系: ProxyConfigデータクラスが正しく動作することを確認"""
        # Given/When: データクラスを直接作成
        config = ProxyConfig(
            url="http://proxy.example.com:3128", username="proxy_user", password="proxy_pass"
        )

        # Then: 属性が正しく設定される
        assert config.url == "http://proxy.example.com:3128"
        assert config.username == "proxy_user"
        assert config.password == "proxy_pass"


class TestEdgeCases:
    """エッジケースのテストクラス"""

    def test_empty_string_values(self, monkeypatch):
        """境界値テスト: 空文字列が設定されている場合にエラーとなることを確認"""
        # Given: 空文字列が設定されている
        monkeypatch.setenv("RAPRAS_USERNAME", "")
        monkeypatch.setenv("RAPRAS_PASSWORD", "test_password")

        # When/Then: ValueErrorが発生する（空文字列はFalsyなのでエラーになる）
        with pytest.raises(ValueError) as exc_info:
            load_rapras_config()

        # Then: エラーメッセージが適切
        assert "RAPRAS_USERNAME" in str(exc_info.value)

    def test_whitespace_values_are_valid(self, monkeypatch):
        """境界値テスト: スペースのみの値は有効とみなされることを確認"""
        # Given: スペースのみの値が設定されている
        monkeypatch.setenv("RAPRAS_USERNAME", "   ")
        monkeypatch.setenv("RAPRAS_PASSWORD", "test_password")

        # When: 設定を読み込み
        config = load_rapras_config()

        # Then: スペースのみの値がそのまま設定される（検証は呼び出し側の責任）
        assert config.username == "   "
        assert config.password == "test_password"
