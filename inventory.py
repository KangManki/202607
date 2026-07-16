import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent / 'inventory.db'


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
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT,
            stock INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    # If table is empty, insert demo products
    cur.execute('SELECT COUNT(*) as c FROM products')
    row = cur.fetchone()
    if row and row['c'] == 0:
        demo = [
            ('Widget A', 'W-A', 100),
            ('Widget B', 'W-B', 50),
            ('Gadget X', 'G-X', 25),
        ]
        cur.executemany('INSERT INTO products (name, sku, stock) VALUES (?, ?, ?)', demo)
        conn.commit()
    conn.close()


def add_product(name, sku=None, stock=0):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (name, sku, stock) VALUES (?, ?, ?)",
        (name, sku, stock),
    )
    conn.commit()
    conn.close()


def list_products():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM products ORDER BY id DESC')
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_stock(product_id, delta):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('UPDATE products SET stock = stock + ? WHERE id=?', (delta, product_id))
    conn.commit()
    conn.close()


def export_products_csv():
    rows = list_products()
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode('utf-8')


def ui():
    initialize_db()
    st.subheader('재고관리')
    df = pd.DataFrame(list_products())
    if df.empty:
        st.info('등록된 상품이 없습니다.')
    else:
        sort_cols = ['id'] + [c for c in df.columns if c != 'id']
        sort_by = st.selectbox('정렬 기준', options=sort_cols, index=0)
        asc = st.checkbox('오름차순', value=False)
        try:
            st.dataframe(df.sort_values(by=sort_by, ascending=asc))
        except Exception:
            st.dataframe(df)

    with st.form('prod_form'):
        name = st.text_input('상품명')
        sku = st.text_input('SKU')
        stock = st.number_input('초기 재고', min_value=0, step=1)
        submit = st.form_submit_button('상품 추가')
        if submit:
            if not name.strip():
                st.error('상품명은 필수입니다.')
            else:
                add_product(name.strip(), sku.strip() or None, int(stock))
                st.success('상품이 추가되었습니다.')

    with st.form('stock_adjust'):
        pid = st.number_input('상품 ID', min_value=0, step=1)
        delta = st.number_input('증감량(음수 가능)', value=0)
        sub = st.form_submit_button('재고 조정')
        if sub:
            user = st.session_state.get('user')
            if pid <= 0:
                st.error('유효한 상품 ID를 입력하세요')
            else:
                if user and user.get('role') == 'admin':
                    update_stock(int(pid), int(delta))
                    st.success('재고가 조정되었습니다.')
                else:
                    st.error('재고 조정 권한이 없습니다 (관리자 전용).')

    st.download_button('상품 CSV 내보내기', data=export_products_csv(), file_name='products.csv', mime='text/csv')
