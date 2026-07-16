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
    q = st.text_input('검색 (이름/이메일/전화)', key='cust_search')
    if q:
        rows = search_customers(q)
    else:
        rows = get_all_customers()
    df = pd.DataFrame(rows)

    if 'selected_customer_id' not in st.session_state:
        st.session_state['selected_customer_id'] = None
    if 'edit_mode' not in st.session_state:
        st.session_state['edit_mode'] = False
    if 'customer_refresh' not in st.session_state:
        st.session_state['customer_refresh'] = False

    if df.empty:
        st.info('등록된 고객이 없습니다.')
    else:
        sort_cols = ['id'] + [c for c in df.columns if c != 'id']
        sort_by = st.selectbox('정렬 기준', options=sort_cols, index=0)
        asc = st.checkbox('오름차순', value=False)
        try:
            sorted_df = df.sort_values(by=sort_by, ascending=asc)
        except Exception:
            sorted_df = df

        grid_state = st.dataframe(
            sorted_df,
            hide_index=True,
            use_container_width=True,
            selection_mode='single-row',
            on_select='rerun',
            key='customer_grid',
        )

        selected_rows = []
        if hasattr(grid_state, 'selection'):
            selected_rows = getattr(grid_state.selection, 'rows', []) or []
        elif isinstance(grid_state, dict):
            selected_rows = grid_state.get('selection', {}).get('rows', []) or []

        if selected_rows:
            row_index = selected_rows[0]
            selected_row = sorted_df.iloc[row_index].to_dict()
            st.session_state['selected_customer_id'] = selected_row.get('id')
            st.session_state['edit_mode'] = True
        else:
            if st.session_state['selected_customer_id'] is not None and not any(r.get('id') == st.session_state['selected_customer_id'] for r in rows):
                st.session_state['selected_customer_id'] = None
                st.session_state['edit_mode'] = False

    selected_customer = None
    if st.session_state['selected_customer_id'] is not None:
        selected_customer = next((r for r in rows if r.get('id') == st.session_state['selected_customer_id']), None)

    with st.expander('고객 추가/수정', expanded=st.session_state['edit_mode']):
        if st.session_state['edit_mode']:
            st.caption('선택한 고객의 값이 아래 입력창에 자동으로 채워집니다.')
        else:
            st.caption('행을 선택하면 수정 폼이 자동으로 열립니다.')
        with st.form('cust_form'):
            cid_value = int(selected_customer['id']) if selected_customer else 0
            cid = st.number_input('ID(수정시 입력)', min_value=0, step=1, value=cid_value)
            name = st.text_input('이름', value=selected_customer['name'] if selected_customer else '')
            email = st.text_input('이메일', value=selected_customer['email'] if selected_customer else '')
            phone = st.text_input('전화', value=selected_customer['phone'] if selected_customer else '')
            submit = st.form_submit_button('저장')
            if submit:
                if cid and cid > 0:
                    if not name.strip():
                        st.error('이름은 필수입니다.')
                    else:
                        update_customer(int(cid), name.strip(), email.strip() or None, phone.strip() or None, None)
                        st.success('수정 완료')
                        st.session_state['selected_customer_id'] = None
                        st.session_state['edit_mode'] = False
                        st.session_state['customer_refresh'] = True
                        st.rerun()
                else:
                    if not name.strip():
                        st.error('이름은 필수입니다.')
                    else:
                        add_customer(name.strip(), email.strip() or None, phone.strip() or None, None)
                        st.success('추가 완료')
                        st.session_state['selected_customer_id'] = None
                        st.session_state['edit_mode'] = False
                        st.session_state['customer_refresh'] = True
                        st.rerun()

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
