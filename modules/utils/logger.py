"""Logging utility module for unified log output."""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """モジュール用Loggerを取得

    Args:
        name: モジュール名（通常は__name__）

    Returns:
        設定済みLogger（INFO/WARNING/ERROR）
    """
    logger = logging.getLogger(name)

    # 既にハンドラが設定されている場合はスキップ（重複防止）
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # コンソールハンドラを作成
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    # フォーマッターを作成（タイムスタンプとモジュール名を含む）
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger
