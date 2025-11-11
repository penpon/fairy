import sqlite3
from typing import Any


def get_user_data(user_id: int) -> list[tuple[Any, ...]]:
    """指定されたユーザーIDのデータを取得します。

    Args:
        user_id (int): 取得するユーザーのID

    Returns:
        list[tuple[Any, ...]]: ユーザーデータのリスト。各行がタプルとして返される。

    Raises:
        sqlite3.Error: データベース操作が失敗した場合
    """
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        # 安全: パラメータ化されたクエリを使用
        query = "SELECT * FROM users WHERE id = ?"
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()
        return result
