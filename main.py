import streamlit as st

from customers import init as init_customers, ui as customers_ui
from orders import initialize_db as init_orders, ui as orders_ui
from inventory import initialize_db as init_inventory, ui as inventory_ui
from products import init as init_products, ui as products_ui
import auth



def initialize_all():
    init_customers()
    init_orders()
    init_inventory()
    init_products()
    auth.initialize_db()


def main():
    st.set_page_config(page_title='ERP (간이)', layout='wide')
    initialize_all()
    st.sidebar.title('메뉴')

    # 로그인 처리
    if 'user' not in st.session_state:
        st.session_state['user'] = None

    if st.session_state['user'] is None:
        with st.sidebar.form('login_form'):
            st.write('### 로그인')
            username = st.text_input('사용자명')
            password = st.text_input('비밀번호', type='password')
            login = st.form_submit_button('로그인')
            if login:
                user = auth.authenticate(username.strip(), password)
                if user:
                    st.session_state['user'] = user
                    st.rerun()
                else:
                    st.error('로그인 실패')
        st.sidebar.markdown('---')
        st.sidebar.write('관리자 계정이 없으면 사이드바 아래에서 생성하세요.')
        with st.sidebar.form('create_admin'):
            st.write('### 관리자 생성')
            cu = st.text_input('새 관리자 사용자명')
            cp = st.text_input('새 관리자 비밀번호', type='password')
            create = st.form_submit_button('생성')
            if create:
                if not cu.strip() or not cp:
                    st.error('입력 필요')
                else:
                    try:
                        auth.create_user(cu.strip(), cp, role='admin')
                        st.success('관리자 생성됨 — 로그인하세요')
                    except Exception as e:
                        st.error(f'오류: {e}')
        return

    user = st.session_state['user']

    st.sidebar.write(f"로그인: {user['username']} ({user['role']})")
    choice = st.sidebar.radio('기능 선택', ['고객관리', '상품관리', '주문관리', '재고관리', '사용자관리' if user['role']=='admin' else ''])
    if choice == '고객관리':
        customers_ui()
    elif choice == '상품관리':
        products_ui()
    elif choice == '주문관리':
        orders_ui()
    elif choice == '재고관리':
        inventory_ui()
    elif choice == '사용자관리':
        # 관리자 전용 UI
        st.subheader('사용자 관리 (관리자)')
        users = auth.list_users()
        st.table(users)
        with st.form('add_user'):
            uname = st.text_input('사용자명')
            pwd = st.text_input('비밀번호', type='password')
            role = st.selectbox('역할', ['user', 'admin'])
            add = st.form_submit_button('추가')
            if add:
                if not uname.strip() or not pwd:
                    st.error('입력 필요')
                else:
                    try:
                        auth.create_user(uname.strip(), pwd, role=role)
                        st.success('사용자 생성')
                    except Exception as e:
                        st.error(f'오류: {e}')
        with st.form('del_user'):
            uid = st.number_input('삭제할 사용자 ID', min_value=0, step=1)
            d = st.form_submit_button('삭제')
            if d:
                if uid <= 0:
                    st.error('유효한 ID 입력')
                else:
                    auth.delete_user(int(uid))
                    st.success('삭제됨')


if __name__ == '__main__':
    main()
