import sqlite3

def get_user_data(user_id):
    try:
        with sqlite3.connect("users.db") as conn:
            with conn.cursor() as cursor:
                query = "SELECT * FROM users WHERE id = ?"
                cursor.execute(query, (user_id,))
                result = cursor.fetchall()
                return result
    except sqlite3.Error as e:
        raise RuntimeError(f"データベースエラー: {e}") from e
