"""Unit tests for SessionManager class."""

import json

import pytest

from modules.scraper.session_manager import SessionManager


class TestSessionManager:
    """SessionManagerのテストクラス"""

    @pytest.fixture
    def temp_session_dir(self, tmp_path):
        """一時的なセッションディレクトリを作成するフィクスチャ"""
        return tmp_path / "test_sessions"

    @pytest.fixture
    def session_manager(self, temp_session_dir):
        """SessionManagerインスタンスを作成するフィクスチャ"""
        return SessionManager(session_dir=str(temp_session_dir))

    @pytest.fixture
    def sample_cookies(self):
        """テスト用のサンプルCookieを作成するフィクスチャ"""
        return [
            {
                "name": "session_id",
                "value": "abc123def456",
                "domain": ".example.com",
                "path": "/",
                "expires": 1234567890.0,
                "httpOnly": True,
                "secure": True,
                "sameSite": "Lax",
            },
            {
                "name": "user_token",
                "value": "xyz789",
                "domain": ".example.com",
                "path": "/",
                "expires": 9876543210.0,
                "httpOnly": False,
                "secure": False,
                "sameSite": "None",
            },
        ]

    def test_save_session_success(self, session_manager, temp_session_dir, sample_cookies):
        """正常系: セッションが正常に保存されることを確認"""
        # Given: サンプルCookieが用意されている
        service_name = "rapras"

        # When: セッションを保存
        session_manager.save_session(service_name, sample_cookies)

        # Then: セッションファイルが作成される
        session_file = temp_session_dir / f"{service_name}_session.json"
        assert session_file.exists()

        # Then: ファイル内容が正しい
        with session_file.open("r", encoding="utf-8") as f:
            saved_cookies = json.load(f)
        assert saved_cookies == sample_cookies

    def test_save_session_creates_directory(self, temp_session_dir, sample_cookies):
        """正常系: セッションディレクトリが存在しない場合に自動作成されることを確認"""
        # Given: セッションディレクトリが存在しない
        assert not temp_session_dir.exists()
        session_manager = SessionManager(session_dir=str(temp_session_dir))

        # When: セッションを保存
        session_manager.save_session("test", sample_cookies)

        # Then: ディレクトリが自動作成される
        assert temp_session_dir.exists()

    def test_save_session_empty_cookies(self, session_manager, temp_session_dir):
        """境界値テスト: 空のCookieリストを保存"""
        # Given: 空のCookieリスト
        empty_cookies = []
        service_name = "test"

        # When: 空のCookieを保存
        session_manager.save_session(service_name, empty_cookies)

        # Then: ファイルが作成され、空のリストが保存される
        session_file = temp_session_dir / f"{service_name}_session.json"
        assert session_file.exists()
        with session_file.open("r", encoding="utf-8") as f:
            saved_cookies = json.load(f)
        assert saved_cookies == []

    def test_load_session_success(self, session_manager, temp_session_dir, sample_cookies):
        """正常系: セッションが正常に読み込まれることを確認"""
        # Given: セッションファイルが保存されている
        service_name = "yahoo"
        session_manager.save_session(service_name, sample_cookies)

        # When: セッションを読み込み
        loaded_cookies = session_manager.load_session(service_name)

        # Then: 保存したCookieと一致する
        assert loaded_cookies == sample_cookies

    def test_load_session_file_not_found(self, session_manager):
        """異常系: セッションファイルが存在しない場合にNoneを返すことを確認"""
        # Given: セッションファイルが存在しない
        service_name = "nonexistent"

        # When: セッションを読み込み
        loaded_cookies = session_manager.load_session(service_name)

        # Then: Noneが返される
        assert loaded_cookies is None

    def test_load_session_corrupted_json(self, session_manager, temp_session_dir, caplog):
        """異常系: JSONが破損している場合にNoneを返し、警告ログを出力することを確認"""
        # Given: 破損したJSONファイルが存在する
        service_name = "corrupted"
        session_file = temp_session_dir / f"{service_name}_session.json"
        temp_session_dir.mkdir(parents=True, exist_ok=True)
        session_file.write_text("{ invalid json content", encoding="utf-8")

        # When: セッションを読み込み
        loaded_cookies = session_manager.load_session(service_name)

        # Then: Noneが返される
        assert loaded_cookies is None

        # Then: 警告ログが出力される
        assert "Session file corrupted" in caplog.text

    def test_session_exists_true(self, session_manager, sample_cookies):
        """正常系: セッションファイルが存在する場合にTrueを返すことを確認"""
        # Given: セッションファイルが保存されている
        service_name = "rapras"
        session_manager.save_session(service_name, sample_cookies)

        # When: セッションの存在を確認
        exists = session_manager.session_exists(service_name)

        # Then: Trueが返される
        assert exists is True

    def test_session_exists_false(self, session_manager):
        """正常系: セッションファイルが存在しない場合にFalseを返すことを確認"""
        # Given: セッションファイルが存在しない
        service_name = "nonexistent"

        # When: セッションの存在を確認
        exists = session_manager.session_exists(service_name)

        # Then: Falseが返される
        assert exists is False

    def test_delete_session_success(self, session_manager, temp_session_dir, sample_cookies):
        """正常系: セッションファイルが正常に削除されることを確認"""
        # Given: セッションファイルが保存されている
        service_name = "yahoo"
        session_manager.save_session(service_name, sample_cookies)
        session_file = temp_session_dir / f"{service_name}_session.json"
        assert session_file.exists()

        # When: セッションを削除
        session_manager.delete_session(service_name)

        # Then: ファイルが削除される
        assert not session_file.exists()

    def test_delete_session_file_not_found(self, session_manager, caplog):
        """正常系: セッションファイルが存在しない場合でもエラーなく処理されることを確認"""
        # Given: セッションファイルが存在しない
        service_name = "nonexistent"

        # When: セッションを削除
        session_manager.delete_session(service_name)

        # Then: エラーは発生せず、情報ログが出力される
        assert "No session file to delete" in caplog.text

    def test_session_manager_with_custom_directory(self, tmp_path, sample_cookies):
        """正常系: カスタムディレクトリパスでSessionManagerが正常に動作することを確認"""
        # Given: カスタムディレクトリパスでSessionManagerを作成
        custom_dir = tmp_path / "custom" / "sessions"
        session_manager = SessionManager(session_dir=str(custom_dir))

        # When: セッションを保存
        service_name = "test"
        session_manager.save_session(service_name, sample_cookies)

        # Then: カスタムディレクトリにファイルが作成される
        session_file = custom_dir / f"{service_name}_session.json"
        assert session_file.exists()

        # Then: セッションが正常に読み込める
        loaded_cookies = session_manager.load_session(service_name)
        assert loaded_cookies == sample_cookies

    def test_save_session_write_error(
        self, session_manager, temp_session_dir, sample_cookies, caplog
    ):
        """異常系: セッション保存時にOSErrorが発生する場合"""
        # Given: ディレクトリ作成後、ファイル書き込みでOSErrorが発生
        from unittest.mock import patch

        service_name = "test"

        with patch("pathlib.Path.open", side_effect=OSError("Disk full")):
            # When: セッションを保存
            session_manager.save_session(service_name, sample_cookies)

            # Then: 警告ログが出力される
            assert "Failed to save session" in caplog.text

    def test_load_session_read_error(self, session_manager, temp_session_dir, caplog):
        """異常系: セッション読み込み時にOSErrorが発生する場合"""
        # Given: セッションファイルが存在するが読み込みでOSErrorが発生
        from unittest.mock import patch

        service_name = "test"
        session_file = temp_session_dir / f"{service_name}_session.json"
        temp_session_dir.mkdir(parents=True, exist_ok=True)
        session_file.write_text('{"test": "data"}', encoding="utf-8")

        with patch("pathlib.Path.open", side_effect=OSError("Permission denied")):
            # When: セッションを読み込み
            result = session_manager.load_session(service_name)

            # Then: Noneが返される
            assert result is None

            # Then: 警告ログが出力される
            assert "Failed to load session" in caplog.text

    def test_delete_session_os_error(
        self, session_manager, temp_session_dir, sample_cookies, caplog
    ):
        """異常系: セッション削除時にOSErrorが発生する場合"""
        # Given: セッションファイルが存在し、削除時にOSErrorが発生
        from unittest.mock import patch

        service_name = "test"
        session_manager.save_session(service_name, sample_cookies)

        with patch("pathlib.Path.unlink", side_effect=OSError("Permission denied")):
            # When: セッションを削除
            session_manager.delete_session(service_name)

            # Then: 警告ログが出力される
            assert "Failed to delete session" in caplog.text
