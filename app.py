import streamlit as st
import pandas as pd

initial_balance = {
    "現金": 1300, "中國信託": 546, "Paypal": 33345, 
    "Linebank": 14392, "玉山銀行": 0, "台新銀行": 0, 
    "國泰世華": 0, "元大銀行": 0, "星展銀行": 0
}

if 'transactions' not in st.session_state:
    st.session_state.transactions = []

st.title("💰 妳的個人多帳戶管理 App")

with st.form("transaction_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        out_acc = st.selectbox("轉出", ["(無)"] + list(initial_balance.keys()))
    with col2:
        in_acc = st.selectbox("轉入", ["(無)"] + list(initial_balance.keys()))
    with col3:
        amount = st.number_input("金額", min_value=0)
    if st.form_submit_button("新增紀錄"):
        st.session_state.transactions.append({"From": out_acc, "To": in_acc, "Amount": amount})

df_tx = pd.DataFrame(st.session_state.transactions)
st.subheader("🏦 目前資金概況")
for bank, initial in initial_balance.items():
    bal = initial
    if not df_tx.empty:
        bal += df_tx[df_tx['To'] == bank]['Amount'].sum() - df_tx[df_tx['From'] == bank]['Amount'].sum()
    st.write(f"**{bank}**: ${bal:,.0f}")
