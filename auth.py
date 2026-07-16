import sqlite3
from pathlib import Path
import os
import hashlib
import binascii

DB_PATH = Path(__file__).parent / 'users.db'


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            pwd_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def _hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    else:
        salt = binascii.unhexlify(salt)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return binascii.hexlify(dk).decode('utf-8'), binascii.hexlify(salt).decode('utf-8')


def create_user(username, password, role='user'):
    initialize_db()
    pwd_hash, salt = _hash_password(password)
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO users (username, pwd_hash, salt, role) VALUES (?, ?, ?, ?)', (username, pwd_hash, salt, role))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise
    conn.close()


def authenticate(username, password):
    initialize_db()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE username=?', (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    stored_hash = row['pwd_hash']
    salt = row['salt']
    attempt_hash, _ = _hash_password(password, salt)
    if attempt_hash == stored_hash:
        return {'id': row['id'], 'username': row['username'], 'role': row['role']}
    return None


def list_users():
    initialize_db()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, username, role FROM users ORDER BY id')
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_user(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM users WHERE id=?', (user_id,))
    conn.commit()
    conn.close()


def get_user_by_username(username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, username, role FROM users WHERE username=?', (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None
