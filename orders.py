import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent / 'orders.db'


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
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            product TEXT,
            quantity INTEGER,
            status TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def add_order(customer_name, product, quantity, status='pending'):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (customer_name, product, quantity, status) VALUES (?, ?, ?, ?)",
        (customer_name, product, quantity, status),
    )
    conn.commit()
    conn.close()


def try_decrement_inventory(product, quantity):
    # try to decrement inventory if inventory DB exists
    try:
        from inventory import get_conn as inv_conn
        conn = inv_conn()
        cur = conn.cursor()
        cur.execute('SELECT id, stock FROM products WHERE name=? OR sku=?', (product, product))
        row = cur.fetchone()
        if row and row['stock'] >= quantity:
            cur.execute('UPDATE products SET stock = stock - ? WHERE id=?', (quantity, row['id']))
            conn.commit()
        conn.close()
    except Exception:
        pass


def list_orders():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM orders ORDER BY id DESC')
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def export_orders_csv():
    rows = list_orders()
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode('utf-8')


def ui():
    initialize_db()
    st.subheader('주문관리')
    df = pd.DataFrame(list_orders())
    if df.empty:
        st.info('등록된 주문이 없습니다.')
    else:
        st.dataframe(df)

    with st.form('order_form'):
        customer_name = st.text_input('고객명')
        product = st.text_input('상품')
        quantity = st.number_input('수량', min_value=1, step=1)
        submit = st.form_submit_button('주문 추가')
        if submit:
            if not customer_name.strip() or not product.strip():
                st.error('고객명과 상품은 필수입니다.')
            else:
                add_order(customer_name.strip(), product.strip(), int(quantity))
                try_decrement_inventory(product.strip(), int(quantity))
                st.success('주문이 추가되었습니다.')

    st.download_button('주문 CSV 내보내기', data=export_orders_csv(), file_name='orders.csv', mime='text/csv')
