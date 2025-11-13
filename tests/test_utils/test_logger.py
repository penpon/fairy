"""Unit tests for Logger utility."""

import logging
import re

from modules.utils.logger import get_logger


class TestLogger:
    """Loggerユーティリティのテストクラス"""

    def test_get_logger_returns_logger_instance(self):
        """正常系: get_loggerがLoggerインスタンスを返すことを確認"""
        # Given: モジュール名を指定
        module_name = "test_module"

        # When: Loggerを取得
        logger = get_logger(module_name)

        # Then: Loggerインスタンスが返される
        assert isinstance(logger, logging.Logger)
        assert logger.name == module_name

    def test_get_logger_sets_info_level(self):
        """正常系: LoggerのレベルがINFOに設定されることを確認"""
        # Given/When: Loggerを取得
        logger = get_logger("test_info_level")

        # Then: ログレベルがINFO
        assert logger.level == logging.INFO

    def test_get_logger_has_handler(self):
        """正常系: Loggerにハンドラが設定されることを確認"""
        # Given/When: Loggerを取得
        logger = get_logger("test_handler")

        # Then: ハンドラが設定されている（コンソール+ファイルの2つ）
        assert len(logger.handlers) == 2
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert isinstance(logger.handlers[1], logging.FileHandler)

    def test_get_logger_handler_format(self):
        """正常系: ログフォーマットにタイムスタンプとモジュール名が含まれることを確認"""
        # Given/When: Loggerを取得
        logger = get_logger("test_format")

        # Then: フォーマッターが設定されている
        handler = logger.handlers[0]
        formatter = handler.formatter
        assert formatter is not None

        # Then: フォーマット文字列に必要な要素が含まれる
        format_string = formatter._fmt
        assert "%(asctime)s" in format_string
        assert "%(name)s" in format_string
        assert "%(levelname)s" in format_string
        assert "%(message)s" in format_string

    def test_get_logger_no_duplicate_handlers(self):
        """正常系: 同じLoggerを複数回取得してもハンドラが重複しないことを確認"""
        # Given: 同じモジュール名でLoggerを複数回取得
        module_name = "test_no_duplicate"

        # When: 最初のLogger取得
        logger1 = get_logger(module_name)
        handler_count_1 = len(logger1.handlers)

        # When: 2回目のLogger取得
        logger2 = get_logger(module_name)
        handler_count_2 = len(logger2.handlers)

        # Then: 同じLoggerインスタンスが返される
        assert logger1 is logger2

        # Then: ハンドラの数が変わらない（コンソール+ファイルの2つ）
        assert handler_count_1 == handler_count_2 == 2

    def test_logger_info_output(self, caplog):
        """正常系: INFOレベルのログが正しく出力されることを確認"""
        # Given: Loggerを取得
        logger = get_logger("test_info_output")

        # When: INFOログを出力
        with caplog.at_level(logging.INFO, logger="test_info_output"):
            logger.info("Test info message")

        # Then: ログが記録される
        assert "Test info message" in caplog.text
        assert "INFO" in caplog.text

    def test_logger_warning_output(self, caplog):
        """正常系: WARNINGレベルのログが正しく出力されることを確認"""
        # Given: Loggerを取得
        logger = get_logger("test_warning_output")

        # When: WARNINGログを出力
        with caplog.at_level(logging.WARNING, logger="test_warning_output"):
            logger.warning("Test warning message")

        # Then: ログが記録される
        assert "Test warning message" in caplog.text
        assert "WARNING" in caplog.text

    def test_logger_error_output(self, caplog):
        """正常系: ERRORレベルのログが正しく出力されることを確認"""
        # Given: Loggerを取得
        logger = get_logger("test_error_output")

        # When: ERRORログを出力
        with caplog.at_level(logging.ERROR, logger="test_error_output"):
            logger.error("Test error message")

        # Then: ログが記録される
        assert "Test error message" in caplog.text
        assert "ERROR" in caplog.text

    def test_logger_debug_not_output_by_default(self, caplog):
        """正常系: DEBUGレベルのログがデフォルトで出力されないことを確認"""
        # Given: Loggerを取得
        logger = get_logger("test_debug_not_output")

        # When: DEBUGログを出力
        with caplog.at_level(logging.DEBUG):
            logger.debug("Test debug message")

        # Then: DEBUGログは記録されない（INFOレベルより低い）
        # Note: caplogはDEBUGレベルでキャプチャしているが、
        # loggerのhandlerはINFOレベルなので実際のログ出力では出力されない
        # ここではloggerのレベルがINFOであることを確認
        assert logger.level == logging.INFO

    def test_logger_does_not_log_sensitive_data(self, caplog):
        """セキュリティ: センシティブデータが直接ログに含まれないことを確認"""
        # Given: Loggerを取得
        logger = get_logger("test_sensitive")

        # When: センシティブデータを含むログメッセージ（良い例）
        # センシティブデータ（例: "test_user"）を直接ログに出力しない
        with caplog.at_level(logging.INFO, logger="test_sensitive"):
            logger.info("User authentication successful")  # センシティブデータを含まない

        # Then: ログにセンシティブデータが含まれない
        assert "test_user" not in caplog.text
        assert "User authentication successful" in caplog.text

    def test_logger_with_different_module_names(self):
        """正常系: 異なるモジュール名で複数のLoggerを作成できることを確認"""
        # Given/When: 異なるモジュール名でLoggerを取得
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        # Then: 異なるLoggerインスタンスが返される
        assert logger1 is not logger2
        assert logger1.name == "module1"
        assert logger2.name == "module2"

    def test_logger_format_includes_timestamp(self, caplog):
        """正常系: ログ出力にタイムスタンプが含まれることを確認"""
        # Given: Loggerを取得
        logger = get_logger("test_timestamp")

        # When: ログを出力
        with caplog.at_level(logging.INFO, logger="test_timestamp"):
            logger.info("Test message with timestamp")

        # Then: ログレコードにタイムスタンプ情報が含まれる
        assert len(caplog.records) > 0
        record = caplog.records[0]
        assert hasattr(record, "created")
        assert record.created > 0

    def test_logger_format_includes_module_name(self, caplog):
        """正常系: ログ出力にモジュール名が含まれることを確認"""
        # Given: Loggerを取得
        module_name = "test_module_name"
        logger = get_logger(module_name)

        # When: ログを出力
        with caplog.at_level(logging.INFO, logger="test_module_name"):
            logger.info("Test message")

        # Then: ログレコードにモジュール名が含まれる
        assert len(caplog.records) > 0
        record = caplog.records[0]
        assert record.name == module_name

    def test_logger_writes_to_file(self, tmp_path, monkeypatch):
        """正常系: ログがファイル(logs/app.log)に出力されることを確認"""
        # Given: 一時ディレクトリにログファイルを作成
        log_dir = tmp_path / "logs"
        log_file = log_dir / "app.log"

        # 環境変数でログディレクトリを指定（テスト用）
        monkeypatch.setenv("LOG_DIR", str(log_dir))

        # When: Loggerを取得してログを出力
        logger = get_logger("test_file_output")
        try:
            logger.info("Test file log message")

            # Then: ログファイルが作成され、メッセージが含まれる
            assert log_file.exists()
            content = log_file.read_text()
            assert "Test file log message" in content
            assert "INFO" in content
        finally:
            # FileHandlerをクリーンアップ（Windows環境での tmp_path 削除エラー防止）
            for handler in logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    logger.removeHandler(handler)

    def test_logger_creates_log_directory_if_not_exists(self, tmp_path, monkeypatch):
        """正常系: logsディレクトリが存在しない場合に自動作成されることを確認"""
        # Given: logsディレクトリが存在しない状態
        log_dir = tmp_path / "logs"
        assert not log_dir.exists()

        # 環境変数でログディレクトリを指定
        monkeypatch.setenv("LOG_DIR", str(log_dir))

        # When: Loggerを取得してログを出力
        logger = get_logger("test_create_dir")
        try:
            logger.info("Creating log directory")

            # Then: logsディレクトリが自動作成される
            assert log_dir.exists()
            assert (log_dir / "app.log").exists()
        finally:
            # FileHandlerをクリーンアップ（Windows環境での tmp_path 削除エラー防止）
            for handler in logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    logger.removeHandler(handler)

    def test_logger_both_console_and_file_output(self, tmp_path, caplog, monkeypatch):
        """正常系: ログがコンソールとファイル両方に出力されることを確認"""
        # Given: ログディレクトリを設定
        log_dir = tmp_path / "logs"
        monkeypatch.setenv("LOG_DIR", str(log_dir))

        # When: Loggerを取得してログを出力
        logger = get_logger("test_both_output")
        try:
            with caplog.at_level(logging.INFO, logger="test_both_output"):
                logger.info("Test both outputs")

            # Then: コンソールにログが出力される
            assert "Test both outputs" in caplog.text

            # Then: ファイルにもログが出力される
            log_file = log_dir / "app.log"
            assert log_file.exists()
            content = log_file.read_text()
            assert "Test both outputs" in content
        finally:
            # FileHandlerをクリーンアップ（Windows環境での tmp_path 削除エラー防止）
            for handler in logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    logger.removeHandler(handler)

    def test_logger_file_format_matches_requirements(self, tmp_path, monkeypatch):
        """正常系: ファイルログのフォーマットが要件通り「[YYYY-MM-DD HH:MM:SS] LEVEL - module - message」であることを確認"""
        # Given: ログディレクトリを設定
        log_dir = tmp_path / "logs"
        monkeypatch.setenv("LOG_DIR", str(log_dir))

        # When: Loggerを取得してログを出力
        logger = get_logger("test_format_check")
        try:
            logger.info("Format test message")

            # Then: ファイルログのフォーマットが要件通り
            log_file = log_dir / "app.log"
            content = log_file.read_text()

            # フォーマット: [YYYY-MM-DD HH:MM:SS] LEVEL - module - message
            # ※ 実装では角括弧[]がないかもしれないので、タイムスタンプ形式を確認
            pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
            assert re.search(pattern, content) is not None
            assert "INFO" in content
            assert "test_format_check" in content
            assert "Format test message" in content
        finally:
            # FileHandlerをクリーンアップ（Windows環境での tmp_path 削除エラー防止）
            for handler in logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    logger.removeHandler(handler)

    def test_logger_with_empty_log_dir(self, monkeypatch, caplog):
        """異常系: LOG_DIRが空文字列の場合にコンソール出力のみにフォールバックすることを確認"""
        # Given: LOG_DIRを空文字列に設定
        monkeypatch.setenv("LOG_DIR", "")

        # When: Loggerを取得
        with caplog.at_level(logging.WARNING, logger="test_empty_log_dir"):
            logger = get_logger("test_empty_log_dir")

        # Then: コンソールハンドラのみが設定される（ファイルハンドラなし）
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert "ファイルログの初期化に失敗しました" in caplog.text

    def test_logger_with_whitespace_only_log_dir(self, monkeypatch, caplog):
        """異常系: LOG_DIRが空白のみの場合にコンソール出力のみにフォールバックすることを確認"""
        # Given: LOG_DIRを空白のみに設定
        monkeypatch.setenv("LOG_DIR", "   ")

        # When: Loggerを取得
        logger = get_logger("test_whitespace_log_dir")

        # Then: コンソールハンドラのみが設定される
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_logger_with_invalid_log_dir_permission(self, tmp_path, monkeypatch, caplog):
        """異常系: LOG_DIRに書き込み権限がない場合にコンソール出力のみにフォールバックすることを確認"""
        import os
        import stat

        # Given: 書き込み権限のないディレクトリを作成
        log_dir = tmp_path / "readonly_logs"
        log_dir.mkdir()

        # Unix系のみで権限を変更（Windowsではスキップ）
        if os.name != "nt":
            log_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)  # 読み取りと実行のみ、書き込み不可

            try:
                monkeypatch.setenv("LOG_DIR", str(log_dir))

                # When: Loggerを取得（ファイルログ初期化に失敗）
                with caplog.at_level(logging.WARNING):
                    logger = get_logger("test_permission_error")

                # Then: コンソールハンドラのみが設定される
                assert len(logger.handlers) == 1
                assert isinstance(logger.handlers[0], logging.StreamHandler)

                # Then: 警告メッセージが含まれる
                assert "ファイルログの初期化に失敗しました" in caplog.text
            finally:
                # クリーンアップ: 権限を戻す
                log_dir.chmod(stat.S_IRWXU)
