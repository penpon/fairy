"""Unit tests for Settings configuration management with python-dotenv."""


import pytest

from modules.config.settings import (
    ProxyConfig,
    RaprasConfig,
    YahooConfig,
    load_dotenv_file,
    load_proxy_config,
    load_rapras_config,
    load_yahoo_config,
)


class TestLoadDotenvFile:
    """load_dotenv_file関数のテストクラス"""

    def test_load_dotenv_file_exists(self, tmp_path, monkeypatch):
        """正常系: .envファイルが存在する場合、正常にロードされることを確認"""
        # Given: .envファイルが存在する
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\n")
        monkeypatch.chdir(tmp_path)

        # When: load_dotenv_file()を呼び出し
        result = load_dotenv_file()

        # Then: Trueが返される
        assert result is True

    def test_load_dotenv_file_not_exists(self, tmp_path, monkeypatch):
        """異常系: .envファイルが存在しない場合、FileNotFoundErrorが発生することを確認"""
        # Given: .envファイルが存在しない
        monkeypatch.chdir(tmp_path)

        # When/Then: FileNotFoundErrorが発生する
        with pytest.raises(FileNotFoundError) as exc_info:
            load_dotenv_file()

        # Then: エラーメッセージが適切
        assert ".env file not found" in str(exc_info.value)
        assert "Please create .env file" in str(exc_info.value)

    def test_load_dotenv_file_with_custom_path(self, tmp_path):
        """正常系: カスタムパスを指定した場合、正常にロードされることを確認"""
        # Given: カスタムパスに.envファイルが存在する
        custom_env = tmp_path / "custom.env"
        custom_env.write_text("CUSTOM_VAR=custom_value\n")

        # When: カスタムパスを指定してload_dotenv_file()を呼び出し
        result = load_dotenv_file(dotenv_path=str(custom_env))

        # Then: Trueが返される
        assert result is True

    def test_load_dotenv_file_custom_path_not_exists(self, tmp_path):
        """異常系: カスタムパスのファイルが存在しない場合、FileNotFoundErrorが発生することを確認"""
        # Given: 存在しないカスタムパスを指定
        custom_path = tmp_path / "nonexistent.env"

        # When/Then: FileNotFoundErrorが発生する
        with pytest.raises(FileNotFoundError) as exc_info:
            load_dotenv_file(dotenv_path=str(custom_path))

        # Then: エラーメッセージが適切
        assert ".env file not found" in str(exc_info.value)


class TestRaprasConfigWithDotenv:
    """RaprasConfig with python-dotenvのテストクラス"""

    def test_load_rapras_config_from_dotenv(self, tmp_path, monkeypatch):
        """正常系: .envファイルからRapras設定が読み込まれることを確認"""
        # Given: .envファイルにRAPRAS設定がある
        env_file = tmp_path / ".env"
        env_file.write_text("RAPRAS_USERNAME=test_user\nRAPRAS_PASSWORD=test_pass\n")
        monkeypatch.chdir(tmp_path)
        # 環境変数をクリア
        monkeypatch.delenv("RAPRAS_USERNAME", raising=False)
        monkeypatch.delenv("RAPRAS_PASSWORD", raising=False)

        # When: load_dotenv_file()を呼び出してから設定をロード
        load_dotenv_file()
        config = load_rapras_config()

        # Then: 正しい設定が返される
        assert isinstance(config, RaprasConfig)
        assert config.username == "test_user"
        assert config.password == "test_pass"

    def test_load_rapras_config_env_override(self, tmp_path, monkeypatch):
        """正常系: 環境変数が.envファイルより優先されることを確認"""
        # Given: .envファイルと環境変数の両方に設定がある
        env_file = tmp_path / ".env"
        env_file.write_text("RAPRAS_USERNAME=file_user\nRAPRAS_PASSWORD=file_pass\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("RAPRAS_USERNAME", "env_user")
        monkeypatch.setenv("RAPRAS_PASSWORD", "env_pass")

        # When: load_dotenv_file()を呼び出してから設定をロード
        load_dotenv_file()
        config = load_rapras_config()

        # Then: 環境変数の値が優先される
        assert config.username == "env_user"
        assert config.password == "env_pass"


class TestYahooConfigWithDotenv:
    """YahooConfig with python-dotenvのテストクラス"""

    def test_load_yahoo_config_from_dotenv(self, tmp_path, monkeypatch):
        """正常系: .envファイルからYahoo設定が読み込まれることを確認"""
        # Given: .envファイルにYAHOO設定がある
        env_file = tmp_path / ".env"
        env_file.write_text("YAHOO_PHONE_NUMBER=09012345678\n")
        monkeypatch.chdir(tmp_path)

        # When: load_dotenv_file()を呼び出してから設定をロード
        load_dotenv_file()
        config = load_yahoo_config()

        # Then: 正しい設定が返される
        assert isinstance(config, YahooConfig)
        assert config.phone_number == "09012345678"


class TestProxyConfigWithDotenv:
    """ProxyConfig with python-dotenvのテストクラス"""

    def test_load_proxy_config_from_dotenv(self, tmp_path, monkeypatch):
        """正常系: .envファイルからプロキシ設定が読み込まれることを確認"""
        # Given: .envファイルにPROXY設定がある
        env_file = tmp_path / ".env"
        env_file.write_text(
            "PROXY_URL=http://proxy.example.com:3128\n"
            "PROXY_USERNAME=proxy_user\n"
            "PROXY_PASSWORD=proxy_pass\n"
        )
        monkeypatch.chdir(tmp_path)

        # When: load_dotenv_file()を呼び出してから設定をロード
        load_dotenv_file()
        config = load_proxy_config()

        # Then: 正しい設定が返される
        assert isinstance(config, ProxyConfig)
        assert config.url == "http://proxy.example.com:3128"
        assert config.username == "proxy_user"
        assert config.password == "proxy_pass"


class TestIntegration:
    """統合テスト"""

    def test_full_workflow_without_dotenv_file(self, tmp_path, monkeypatch):
        """異常系: .envファイルなしでload_dotenv_file()を呼ぶとエラーになることを確認"""
        # Given: .envファイルが存在しない
        monkeypatch.chdir(tmp_path)

        # When/Then: FileNotFoundErrorが発生する
        with pytest.raises(FileNotFoundError):
            load_dotenv_file()

    def test_full_workflow_with_dotenv_file(self, tmp_path, monkeypatch):
        """正常系: .envファイルから全設定が読み込まれることを確認"""
        # Given: .envファイルに全設定がある
        env_file = tmp_path / ".env"
        env_file.write_text(
            "RAPRAS_USERNAME=test_user\n"
            "RAPRAS_PASSWORD=test_pass\n"
            "YAHOO_PHONE_NUMBER=09012345678\n"
            "PROXY_URL=http://proxy.example.com:3128\n"
            "PROXY_USERNAME=proxy_user\n"
            "PROXY_PASSWORD=proxy_pass\n"
        )
        monkeypatch.chdir(tmp_path)
        # 環境変数をクリア
        monkeypatch.delenv("RAPRAS_USERNAME", raising=False)
        monkeypatch.delenv("RAPRAS_PASSWORD", raising=False)
        monkeypatch.delenv("YAHOO_PHONE_NUMBER", raising=False)
        monkeypatch.delenv("PROXY_URL", raising=False)
        monkeypatch.delenv("PROXY_USERNAME", raising=False)
        monkeypatch.delenv("PROXY_PASSWORD", raising=False)

        # When: load_dotenv_file()を呼び出してから全設定をロード
        load_dotenv_file()
        rapras_config = load_rapras_config()
        yahoo_config = load_yahoo_config()
        proxy_config = load_proxy_config()

        # Then: 全ての設定が正しく読み込まれる
        assert rapras_config.username == "test_user"
        assert rapras_config.password == "test_pass"
        assert yahoo_config.phone_number == "09012345678"
        assert proxy_config.url == "http://proxy.example.com:3128"
        assert proxy_config.username == "proxy_user"
        assert proxy_config.password == "proxy_pass"
