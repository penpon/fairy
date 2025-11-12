"""Logging utility module for unified log output."""

import logging
import os
import sys
from pathlib import Path

# デフォルトログ設定
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "app.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """モジュール用Loggerを取得

    INFO/WARNING/ERRORレベルのログを、コンソールとファイル(logs/app.log)の
    両方に出力する設定済みLoggerを返します。

    ログフォーマット: "YYYY-MM-DD HH:MM:SS - module - LEVEL - message"
    日本語メッセージをサポートしており、エラーメッセージは日本語で記録できます。

    Args:
        name: モジュール名（通常は__name__）

    Returns:
        設定済みLogger（INFO/WARNING/ERROR）

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("処理を開始しました")
        >>> logger.warning("警告: 設定が不完全です")
        >>> logger.error("エラー: ファイルが見つかりません")
    """
    logger = logging.getLogger(name)

    # 既にハンドラが設定されている場合はスキップ（重複防止）
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # フォーマッターを作成（タイムスタンプとモジュール名を含む）
    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # コンソールハンドラを作成
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラを作成
    log_dir_env = os.environ.get("LOG_DIR", DEFAULT_LOG_DIR)

    # LOG_DIRのバリデーション
    try:
        log_dir = Path(log_dir_env).resolve()

        # 空のパスや不正なパスを拒否
        if not log_dir_env or log_dir_env.strip() == "":
            raise ValueError("LOG_DIR cannot be empty")

        # ディレクトリ作成とファイルハンドラの設定
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / DEFAULT_LOG_FILE

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    except (OSError, PermissionError, ValueError) as e:
        # ファイルログの初期化に失敗した場合はコンソールのみにフォールバック
        logger.warning(f"Failed to initialize file logging: {e}. Using console-only output.")

    return logger
