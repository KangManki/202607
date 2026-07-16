import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).parent / "customers.db"

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
		CREATE TABLE IF NOT EXISTS customers (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL,
			email TEXT,
			phone TEXT,
			notes TEXT
		)
		"""
	)
	conn.commit()
	conn.close()

def add_customer(name, email=None, phone=None, notes=None):
	conn = get_conn()
	cur = conn.cursor()
	cur.execute(
		"INSERT INTO customers (name, email, phone, notes) VALUES (?, ?, ?, ?)",
		(name, email, phone, notes),
	)
	conn.commit()
	conn.close()

def update_customer(customer_id, name, email, phone, notes):
	conn = get_conn()
	cur = conn.cursor()
	cur.execute(
		"UPDATE customers SET name=?, email=?, phone=?, notes=? WHERE id=?",
		(name, email, phone, notes, customer_id),
	)
	conn.commit()
	conn.close()

def delete_customer(customer_id):
	conn = get_conn()
	cur = conn.cursor()
	cur.execute("DELETE FROM customers WHERE id=?", (customer_id,))
	conn.commit()
	conn.close()

def get_all_customers():
	conn = get_conn()
	cur = conn.cursor()
	cur.execute("SELECT * FROM customers ORDER BY id DESC")
	rows = cur.fetchall()
	conn.close()
	return [dict(r) for r in rows]

def search_customers(query):
	q = f"%{query}%"
	conn = get_conn()
	cur = conn.cursor()
	cur.execute(
		"SELECT * FROM customers WHERE name LIKE ? OR email LIKE ? OR phone LIKE ? OR notes LIKE ? ORDER BY id DESC",
		(q, q, q, q),
	)
	rows = cur.fetchall()
	conn.close()
	return [dict(r) for r in rows]

def import_csv(file_like):
	# expects a file-like object (uploaded file)
	df = pd.read_csv(file_like)
	# normalize columns: name,email,phone,notes
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

if __name__ == '__main__':
	initialize_db()
	print('customers.db initialized at', DB_PATH)
