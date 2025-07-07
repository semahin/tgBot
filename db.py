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
