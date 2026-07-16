import pandas as pd
import mysql.connector
from db_config import get_db_config


def get_conn():
    config = get_db_config()
    return mysql.connector.connect(**config)


def initialize_db():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    phone VARCHAR(20),
                    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        conn.commit()
    finally:
        conn.close()


def add_customer(name, email=None, phone=None, notes=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO customers (name, email, phone) VALUES (%s, %s, %s)",
                (name, email, phone),
            )
        conn.commit()
    finally:
        conn.close()


def update_customer(customer_id, name, email, phone, notes):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE customers SET name=%s, email=%s, phone=%s WHERE customer_id=%s",
                (name, email, phone, customer_id),
            )
        conn.commit()
    finally:
        conn.close()


def delete_customer(customer_id):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM customers WHERE customer_id=%s", (customer_id,))
        conn.commit()
    finally:
        conn.close()


def get_all_customers():
    conn = get_conn()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT customer_id AS id, name, email, phone, create_at AS created_at FROM customers ORDER BY customer_id DESC")
            rows = cur.fetchall()
        return rows
    finally:
        conn.close()


def search_customers(query):
    q = f"%{query}%"
    conn = get_conn()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT customer_id AS id, name, email, phone, create_at AS created_at FROM customers WHERE name LIKE %s OR email LIKE %s OR phone LIKE %s ORDER BY customer_id DESC",
                (q, q, q),
            )
            rows = cur.fetchall()
        return rows
    finally:
        conn.close()


def import_csv(file_like):
    df = pd.read_csv(file_like)
    cols = [c.lower() for c in df.columns]
    mapping = {}
    for col in cols:
        if 'name' in col:
            mapping[col] = 'name'
        elif 'email' in col:
            mapping[col] = 'email'
        elif 'phone' in col or 'tel' in col:
            mapping[col] = 'phone'
        elif 'note' in col:
            mapping[col] = 'notes'
    df = df.rename(columns=mapping)
    for _, row in df.iterrows():
        name = row.get('name')
        if pd.isna(name) or name is None:
            continue
        add_customer(
            str(name),
            str(row.get('email')) if not pd.isna(row.get('email')) else None,
            str(row.get('phone')) if not pd.isna(row.get('phone')) else None,
            str(row.get('notes')) if not pd.isna(row.get('notes')) else None,
        )


def export_csv():
    rows = get_all_customers()
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode('utf-8')
