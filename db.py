import sqlite3
from datetime import datetime

DB_NAME = 'users.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            start_date TEXT,
            email TEXT,
            full_name TEXT,
            username TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, full_name=None, username=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if c.fetchone() is None:
        c.execute(
            'INSERT INTO users (user_id, start_date, full_name, username) VALUES (?, ?, ?, ?)',
            (user_id, datetime.now().isoformat(), full_name, username)
        )
        conn.commit()
    conn.close()

def user_exists(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def set_email(user_id, email):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE users SET email = ? WHERE user_id = ?', (email, user_id))
    conn.commit()
    conn.close()

def get_user_start_date(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT start_date FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT user_id, start_date, email FROM users')
    users = c.fetchall()
    conn.close()
    return users

def get_user_email(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT email FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None
