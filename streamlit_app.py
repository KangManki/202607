import streamlit as st
import pandas as pd
from customers_db import (
    initialize_db,
    add_customer,
    get_all_customers,
    update_customer,
    delete_customer,
    search_customers,
    import_csv,
    export_csv,
)


initialize_db()


st.set_page_config(page_title='고객관리', layout='wide')


def show_sidebar():
    st.sidebar.title('고객관리')
    menu = st.sidebar.radio('메뉴', ['목록 보기', '고객 추가', '가져오기(CSV)', '내보내기(CSV)'])
    return menu


def view_customers():
    st.header('고객 목록')
    q = st.text_input('검색 (이름/이메일/전화)')
    if q:
        rows = search_customers(q)
    else:
        rows = get_all_customers()
    df = pd.DataFrame(rows)
    if df.empty:
        st.info('등록된 고객이 없습니다.')
        return
    st.dataframe(df)

    cols = st.columns([1, 1, 2])
    with cols[0]:
        st.subheader('편집')
        ids = df['id'].tolist()
        selected = st.selectbox('편집할 고객 ID 선택', options=ids)
        if st.button('불러오기'):
            cust = [r for r in rows if r['id'] == selected][0]
            st.session_state['edit'] = cust

    if 'edit' in st.session_state:
        cust = st.session_state['edit']
        st.subheader('고객 수정')
        with st.form('edit_form'):
            name = st.text_input('이름', value=cust.get('name', ''))
            email = st.text_input('이메일', value=cust.get('email', ''))
            phone = st.text_input('전화', value=cust.get('phone', ''))
            submitted = st.form_submit_button('저장')
            if submitted:
                update_customer(cust['id'], name, email, phone, None)
                st.success('수정되었습니다.')
                del st.session_state['edit']

    st.subheader('삭제')
    ids = df['id'].tolist()
    to_delete = st.selectbox('삭제할 고객 ID 선택', options=[None] + ids)
    if to_delete:
        if st.button('삭제'):
            delete_customer(int(to_delete))
            st.success('삭제되었습니다.')


def add_customer_ui():
    st.header('고객 추가')
    with st.form('add_form'):
        name = st.text_input('이름')
        email = st.text_input('이메일')
        phone = st.text_input('전화')
        submitted = st.form_submit_button('추가')
        if submitted:
            if not name.strip():
                st.error('이름은 필수입니다.')
            else:
                add_customer(name.strip(), email.strip() or None, phone.strip() or None, None)
                st.success('고객이 추가되었습니다.')


def import_ui():
    st.header('CSV 가져오기')
    file = st.file_uploader('CSV 파일 업로드', type=['csv'])
    if file is not None:
        try:
            import_csv(file)
            st.success('가져오기가 완료되었습니다.')
        except Exception as e:
            st.error(f'가져오기 중 오류: {e}')


def export_ui():
    st.header('CSV 내보내기')
    csv_bytes = export_csv()
    st.download_button('CSV 다운로드', data=csv_bytes, file_name='customers.csv', mime='text/csv')


def main():
    menu = show_sidebar()
    if menu == '목록 보기':
        view_customers()
    elif menu == '고객 추가':
        add_customer_ui()
    elif menu == '가져오기(CSV)':
        import_ui()
    elif menu == '내보내기(CSV)':
        export_ui()


if __name__ == '__main__':
    main()
