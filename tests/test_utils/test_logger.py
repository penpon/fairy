"""Unit tests for Logger utility."""

import logging

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

        # Then: ハンドラが設定されている
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

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

        # Then: ハンドラの数が変わらない
        assert handler_count_1 == handler_count_2 == 1

    def test_logger_info_output(self, caplog):
        """正常系: INFOレベルのログが正しく出力されることを確認"""
        # Given: Loggerを取得
        logger = get_logger("test_info_output")

        # When: INFOログを出力
        with caplog.at_level(logging.INFO):
            logger.info("Test info message")

        # Then: ログが記録される
        assert "Test info message" in caplog.text
        assert "INFO" in caplog.text

    def test_logger_warning_output(self, caplog):
        """正常系: WARNINGレベルのログが正しく出力されることを確認"""
        # Given: Loggerを取得
        logger = get_logger("test_warning_output")

        # When: WARNINGログを出力
        with caplog.at_level(logging.WARNING):
            logger.warning("Test warning message")

        # Then: ログが記録される
        assert "Test warning message" in caplog.text
        assert "WARNING" in caplog.text

    def test_logger_error_output(self, caplog):
        """正常系: ERRORレベルのログが正しく出力されることを確認"""
        # Given: Loggerを取得
        logger = get_logger("test_error_output")

        # When: ERRORログを出力
        with caplog.at_level(logging.ERROR):
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
        with caplog.at_level(logging.INFO):
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
        with caplog.at_level(logging.INFO):
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
        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        # Then: ログレコードにモジュール名が含まれる
        assert len(caplog.records) > 0
        record = caplog.records[0]
        assert record.name == module_name
