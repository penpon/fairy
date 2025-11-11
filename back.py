import sqlite3
from pathlib import Path
from typing import Any


def get_user_data(user_id: int, db_path: str | Path = "users.db") -> list[tuple[Any, ...]]:
    """指定されたユーザーIDのデータを取得します。

    Args:
        user_id: 取得するユーザーのID
        db_path: データベースファイルのパス（デフォルト: "users.db"）

    Returns:
        ユーザーデータのタプルのリスト

    Raises:
        sqlite3.Error: データベース操作でエラーが発生した場合
        ValueError: user_idが無効な場合
    """
    if user_id < 0:
        raise ValueError("user_id must be non-negative")

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()

        # 安全: パラメータ化クエリを使用
        query = "SELECT * FROM users WHERE id = ?"
        cursor.execute(query, (user_id,))

        result = cursor.fetchall()
        return result
