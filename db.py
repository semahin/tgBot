import sqlite3

def init_db():
    with sqlite3.connect("purchases.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                price TEXT,
                customer TEXT,
                date TEXT,
                deadline TEXT
            )
        """)
        conn.commit()

def save_purchase(user_id, name, price, customer, date, deadline):
    with sqlite3.connect("purchases.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO saved_purchases (user_id, name, price, customer, date, deadline)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, name, price, customer, date, deadline))
        conn.commit()

def get_user_purchases(user_id):
    with sqlite3.connect("purchases.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, price, customer, date, deadline
            FROM saved_purchases
            WHERE user_id = ?
        """, (user_id,))
        return cursor.fetchall()

def delete_purchase(user_id: int, purchase_id: int):
    with sqlite3.connect("purchases.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM saved_purchases
            WHERE user_id = ? AND id = ?
        """, (user_id, purchase_id))
        conn.commit()

def get_user_purchase_by_index(user_id, index):
    with sqlite3.connect("purchases.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, price, customer, date, deadline
            FROM saved_purchases
            WHERE user_id = ?
            ORDER BY id
        """, (user_id,))
        rows = cursor.fetchall()
        if 0 <= index < len(rows):
            return rows[index], len(rows)
        return None, len(rows)

