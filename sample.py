import sqlite3
import logging
from typing import List, Tuple, Any

logger = logging.getLogger(__name__)


def get_user_data(user_id: int) -> List[Tuple[Any, ...]]:
    """指定されたユーザーIDのデータをデータベースから取得します。

    Args:
        user_id (int): 取得するユーザーのID

    Returns:
        List[Tuple[Any, ...]]: ユーザーデータのタプルのリスト

    Raises:
        sqlite3.Error: データベース操作が失敗した場合
    """
    try:
        # コンテキストマネージャーで安全にリソースを管理
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            # 安全: パラメータ化クエリを使用
            query = "SELECT * FROM users WHERE id = ?"
            cursor.execute(query, (user_id,))
            result = cursor.fetchall()
            return result
    except sqlite3.Error as e:
        logger.error(f"Database error occurred: {e}")
        raise
