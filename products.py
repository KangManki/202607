import streamlit as st
import pandas as pd
from customers_db import get_conn as get_customer_conn


def init():
    conn = get_customer_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS product (
                    product_id INT AUTO_INCREMENT PRIMARY KEY,
                    product_name VARCHAR(100) NOT NULL,
                    price DECIMAL(10,2) NOT NULL DEFAULT 0,
                    stock_quantity INT NOT NULL DEFAULT 0,
                    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        conn.commit()
    finally:
        conn.close()


def get_all_products():
    conn = get_customer_conn()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT product_id AS id, product_name AS name, price, stock_quantity AS stock, last_updated AS updated_at FROM product ORDER BY product_id DESC"
            )
            return cur.fetchall()
    finally:
        conn.close()


def search_products(query):
    q = f"%{query}%"
    conn = get_customer_conn()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT product_id AS id, product_name AS name, price, stock_quantity AS stock, last_updated AS updated_at FROM product WHERE product_name LIKE %s ORDER BY product_id DESC",
                (q,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def add_product(name, price, stock):
    conn = get_customer_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO product (product_name, price, stock_quantity) VALUES (%s, %s, %s)",
                (name, price, stock),
            )
        conn.commit()
    finally:
        conn.close()


def update_product(product_id, name, price, stock):
    conn = get_customer_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE product SET product_name=%s, price=%s, stock_quantity=%s WHERE product_id=%s",
                (name, price, stock, product_id),
            )
        conn.commit()
    finally:
        conn.close()


def delete_product(product_id):
    conn = get_customer_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM product WHERE product_id=%s", (product_id,))
        conn.commit()
    finally:
        conn.close()


def ui():
    st.subheader('상품관리')
    q = st.text_input('검색 (상품명)', key='product_search')
    if q:
        rows = search_products(q)
    else:
        rows = get_all_products()

    df = pd.DataFrame(rows)
    if df.empty:
        st.info('등록된 상품이 없습니다.')
    else:
        st.dataframe(df, hide_index=True, use_container_width=True)

    if 'selected_product_id' not in st.session_state:
        st.session_state['selected_product_id'] = None
    if 'product_edit_mode' not in st.session_state:
        st.session_state['product_edit_mode'] = False

    if st.session_state['selected_product_id'] is not None:
        selected_product = next((r for r in rows if r.get('id') == st.session_state['selected_product_id']), None)
    else:
        selected_product = None

    if st.button('선택한 상품 수정', disabled=st.session_state['selected_product_id'] is None):
        st.session_state['product_edit_mode'] = True

    if st.session_state['product_edit_mode'] and selected_product:
        st.markdown('---')
        st.subheader('상품 수정')
        with st.form('product_edit_form'):
            pid = st.text_input('상품 ID', value=str(selected_product['id']))
            name = st.text_input('상품명', value=selected_product['name'])
            price = st.number_input('가격', value=float(selected_product['price']), min_value=0.0, step=1000.0)
            stock = st.number_input('재고', value=int(selected_product['stock']), min_value=0, step=1)
            save = st.form_submit_button('저장')
            cancel = st.form_submit_button('취소')
            if save:
                update_product(int(pid), name.strip(), price, stock)
                st.success('수정되었습니다.')
                st.session_state['selected_product_id'] = None
                st.session_state['product_edit_mode'] = False
                st.rerun()
            if cancel:
                st.session_state['selected_product_id'] = None
                st.session_state['product_edit_mode'] = False
                st.rerun()
    else:
        st.markdown('---')
        st.subheader('상품 추가')
        with st.form('product_add_form'):
            name = st.text_input('상품명')
            price = st.number_input('가격', min_value=0.0, step=1000.0)
            stock = st.number_input('재고', min_value=0, step=1)
            submit = st.form_submit_button('추가')
            if submit:
                if not name.strip():
                    st.error('상품명은 필수입니다.')
                else:
                    add_product(name.strip(), price, stock)
                    st.success('상품이 추가되었습니다.')
                    st.rerun()

    st.markdown('---')
    if rows:
        ids = [r['id'] for r in rows]
        selected_id = st.selectbox('삭제할 상품 ID 선택', options=[None] + ids)
        if selected_id:
            if st.button('삭제'):
                delete_product(int(selected_id))
                st.success('삭제되었습니다.')
                st.rerun()
