import os
import sqlite3
import hashlib

# ハードコードされた認証情報（セキュリティ問題）
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "admin123"


def get_user_data(user_id):
    # SQL Injection脆弱性のある関数
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # 危険: ユーザー入力を直接SQLに埋め込んでいる
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)

    result = cursor.fetchall()
    return result
