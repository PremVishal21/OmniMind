import sqlite3
import hashlib
import json
import os

DB_FILE = "omnimind.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            history TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return True, "User created successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[1] == hash_password(password):
        return True, row[0]
    return False, None

def save_chat_history(user_id, history_list):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check if a chat entry already exists for this user
    # For simplicity, we store the entire history list as JSON in a single row per user
    c.execute("SELECT id FROM chats WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    
    # We shouldn't store large base64 image strings in the history if possible, but for now we JSON dump it.
    history_json = json.dumps(history_list)
    
    if row:
        c.execute("UPDATE chats SET history = ? WHERE user_id = ?", (history_json, user_id))
    else:
        c.execute("INSERT INTO chats (user_id, history) VALUES (?, ?)", (user_id, history_json))
    
    conn.commit()
    conn.close()

def get_chat_history(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT history FROM chats WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return []
