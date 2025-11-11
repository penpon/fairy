import sqlite3


def get_user_data(user_id: int) -> list[tuple]:
    """指定されたユーザーIDのデータを取得します。

    Args:
        user_id: 取得するユーザーのID

    Returns:
        ユーザーデータのタプルのリスト

    Raises:
        sqlite3.Error: データベース操作でエラーが発生した場合
    """
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()

        # 安全: パラメータ化クエリを使用
        query = "SELECT * FROM users WHERE id = ?"
        cursor.execute(query, (user_id,))

        result = cursor.fetchall()
        return result
