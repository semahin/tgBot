import sqlite3
import pandas as pd

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_purchases (
                id TEXT,
                user_id INTEGER,
                PRIMARY KEY (id, user_id)
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
        """, (user_id,))
        rows = cursor.fetchall()
        if 0 <= index < len(rows):
            return rows[index], len(rows)
        return None, len(rows)
    
def get_new_records_from_db(df, user_id: int, id_column="Реестровый номер закупки"):
    ids_in_csv = df[id_column].astype(str)
    new_rows = []

    conn = sqlite3.connect("purchases.db")
    cursor = conn.cursor()

    for idx, record_id in enumerate(ids_in_csv):
        cursor.execute("SELECT 1 FROM scheduled_purchases WHERE id = ? AND user_id = ?", (record_id, user_id))
        if not cursor.fetchone():
            new_rows.append(idx)

    conn.close()

    return df.iloc[new_rows]

def save_scheduled_purchase(row, user_id: int):
    conn = sqlite3.connect("purchases.db")
    cursor = conn.cursor()

    purchase_id = str(row.get("Реестровый номер закупки", ""))

    if purchase_id:
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO scheduled_purchases (id, user_id) VALUES (?, ?)",
                (purchase_id, user_id)
            )
            conn.commit()
        except Exception as e:
            print(f"[DB] ❌ Ошибка при сохранении просмотренной закупки: {e}")
    
    conn.close()

def get_new_records_for_user(df, user_id):
    try:
        conn = sqlite3.connect("purchases.db")
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM scheduled_purchases WHERE user_id = ?", (user_id,))
        seen_ids = {row[0] for row in cursor.fetchall()}

        current_ids = set(df["Реестровый номер закупки"].astype(str))
        new_ids = current_ids - seen_ids

        new_df = df[df["Реестровый номер закупки"].astype(str).isin(new_ids)]

        return new_df
    except Exception as e:
        print(f"[get_new_records_for_user] ❌ Ошибка: {e}")
        return pd.DataFrame()
    
def clear_scheduled_purchases(user_id: int):
    conn = sqlite3.connect("purchases.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scheduled_purchases WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()