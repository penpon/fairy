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


def process_user_input(data):
    # 型ヒントなし、エラーハンドリングなし
    # 複雑すぎる関数（複数の責任を持っている）

    if data:
        if len(data) > 0:
            if isinstance(data, dict):
                if "username" in data:
                    if data["username"]:
                        if len(data["username"]) > 3:
                            if data["username"].isalnum():
                                # ネストが深すぎる
                                result = []
                                for i in range(len(data)):
                                    result.append(data[i])
                                return result
    return None


def hash_password(password):
    # 弱いハッシュアルゴリズム（MD5は非推奨）
    return hashlib.md5(password.encode()).hexdigest()


class DataProcessor:
    def __init__(self):
        self.data = []
        self.cache = {}

    def add_data(self, item):
        # パフォーマンス問題: リストの先頭に挿入
        self.data.insert(0, item)

    def find_item(self, value):
        # パフォーマンス問題: 毎回全件検索
        for item in self.data:
            if item == value:
                return item
        return None

    def process_all(self):
        # 重複コード
        result = []
        for item in self.data:
            processed = item.upper() if isinstance(item, str) else str(item)
            result.append(processed)
        return result

    def process_filtered(self, condition):
        # 重複コード（process_allと似ている）
        result = []
        for item in self.data:
            if condition(item):
                processed = item.upper() if isinstance(item, str) else str(item)
                result.append(processed)
        return result


def execute_command(cmd):
    # セキュリティ問題: コマンドインジェクション脆弱性
    os.system(cmd)


def divide_numbers(a, b):
    # エラーハンドリングなし（ゼロ除算）
    return a / b


# グローバル変数の乱用
counter = 0
temp_data = []
user_session = {}


def increment_counter():
    global counter
    counter += 1


def update_session(key, value):
    global user_session
    user_session[key] = value


# マジックナンバーの使用
def calculate_price(base_price):
    tax = base_price * 0.1  # マジックナンバー
    shipping = 500  # マジックナンバー
    total = base_price + tax + shipping
    return total


# 長すぎる関数（単一責任の原則違反）
def process_order(order_data):
    # バリデーション
    if not order_data.get("customer_id"):
        return None

    # 価格計算
    items = order_data.get("items", [])
    total = 0
    for item in items:
        total += item["price"] * item["quantity"]

    # 税金計算
    tax = total * 0.1

    # 送料計算
    if total > 10000:
        shipping = 0
    else:
        shipping = 500

    # 割引計算
    discount = 0
    if order_data.get("coupon"):
        discount = total * 0.05

    # 最終金額
    final_total = total + tax + shipping - discount

    # データベース保存
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO orders VALUES ({order_data['customer_id']}, {final_total})")
    conn.commit()

    # メール送信（簡略化）
    print(f"Order confirmation sent to customer {order_data['customer_id']}")

    return final_total

