# database.py
import sqlite3

def init_db():
    conn = sqlite3.connect('logistics_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            weight REAL,
            length REAL,
            width REAL,
            height REAL,
            origin TEXT,
            destination TEXT,
            distance TEXT,
            duration TEXT,
            cost REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_order(chat_id, order_data):
    conn = sqlite3.connect('logistics_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (chat_id, weight, length, width, height, origin, destination, distance, duration, cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        chat_id,
        order_data['weight'],
        order_data.get('dimensions', (0, 0, 0))[0],
        order_data.get('dimensions', (0, 0, 0))[1],
        order_data.get('dimensions', (0, 0, 0))[2],
        order_data['origin'],
        order_data['destination'],
        order_data['distance'],
        order_data['duration'],
        order_data['cost']
    ))
    conn.commit()
    conn.close()

def get_orders(chat_id):
    conn = sqlite3.connect('logistics_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT weight, length, width, height, origin, destination, distance, duration, cost
        FROM orders
        WHERE chat_id = ?
    ''', (chat_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders
