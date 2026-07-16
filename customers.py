import streamlit as st
import pandas as pd
from customers_db import (
    initialize_db as init_customers_db,
    add_customer,
    get_all_customers,
    update_customer,
    delete_customer,
    search_customers,
    import_csv,
    export_csv,
)


def init():
    init_customers_db()


def ui():
    st.subheader('고객관리')
    q = st.text_input('검색 (이름/이메일/전화/메모)', key='cust_search')
    if q:
        rows = search_customers(q)
    else:
        rows = get_all_customers()
    df = pd.DataFrame(rows)
    if df.empty:
        st.info('등록된 고객이 없습니다.')
    else:
        # 정렬 옵션
        sort_cols = ['id'] + [c for c in df.columns if c != 'id']
        sort_by = st.selectbox('정렬 기준', options=sort_cols, index=0)
        asc = st.checkbox('오름차순', value=False)
        try:
            st.dataframe(df.sort_values(by=sort_by, ascending=asc))
        except Exception:
            st.dataframe(df)

    with st.expander('고객 추가/수정'):
        with st.form('cust_form'):
            cid = st.number_input('ID(수정시 입력)', min_value=0, step=1)
            name = st.text_input('이름')
            email = st.text_input('이메일')
            phone = st.text_input('전화')
            notes = st.text_area('메모')
            submit = st.form_submit_button('저장')
            if submit:
                user = st.session_state.get('user')
                if cid and cid > 0:
                    # 수정 권한: admin 또는 본인(간단히 허용)
                    if user and user.get('role') in ('admin',):
                        update_customer(int(cid), name, email or None, phone or None, notes or None)
                        st.success('수정 완료')
                    else:
                        st.error('수정 권한이 없습니다.')
                else:
                    if not name.strip():
                        st.error('이름은 필수입니다.')
                    else:
                        add_customer(name.strip(), email.strip() or None, phone.strip() or None, notes.strip() or None)
                        st.success('추가 완료')

    st.markdown('---')
    uploaded = st.file_uploader('CSV 가져오기', type=['csv'])
    if uploaded is not None:
        import_csv(uploaded)
        st.success('가져오기 완료')

    csv_bytes = export_csv()
    st.download_button('고객 CSV 내보내기', data=csv_bytes, file_name='customers.csv', mime='text/csv')

    # 삭제는 관리자만
    st.markdown('---')
    user = st.session_state.get('user')
    if user and user.get('role') == 'admin':
        ids = [r['id'] for r in rows]
        to_del = st.selectbox('삭제할 고객 ID 선택 (관리자 전용)', options=[None] + ids)
        if to_del:
            if st.button('삭제(관리자)'):
                delete_customer(int(to_del))
                st.success('삭제되었습니다.')
    else:
        st.info('삭제는 관리자만 가능합니다.')
