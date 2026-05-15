import streamlit as st
import pandas as pd

# 1. 妳的 9 個帳戶初始資金
initial_balance = {
    "現金": 1300, "中國信託": 546, "Paypal": 33345, 
    "Linebank": 14392, "玉山銀行": 0, "台新銀行": 0, 
    "國泰世華": 0, "元大銀行": 0, "星展銀行": 0
}

# 2. 初始化交易紀錄
if 'transactions' not in st.session_state:
    st.session_state.transactions = []

st.title("💰 妳的個人多帳戶管理 App V2")

# 3. 新增紀錄功能
with st.form("transaction_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        out_acc = st.selectbox("轉出帳戶", ["(無)"] + list(initial_balance.keys()))
    with col2:
        in_acc = st.selectbox("轉入帳戶", ["(無)"] + list(initial_balance.keys()))
    with col3:
        amount = st.number_input("金額", min_value=0)
    
    if st.form_submit_button("新增紀錄"):
        st.session_state.transactions.append({
            "From": out_acc, 
            "To": in_acc, 
            "Amount": amount
        })
        st.rerun()

# 4. 計算與加總功能 (邏輯核心)
df_tx = pd.DataFrame(st.session_state.transactions)
balances = {}
total_assets = 0

for bank, initial in initial_balance.items():
    current = initial
    if not df_tx.empty:
        in_sum = df_tx[df_tx['To'] == bank]['Amount'].sum()
        out_sum = df_tx[df_tx['From'] == bank]['Amount'].sum()
        current += (in_sum - out_sum)
    balances[bank] = current
    total_assets += current

# 5. 顯示總資產 (加總功能)
st.metric(label="📊 目前總資產 (TWD)", value=f"${total_assets:,.0f}")

st.divider()

# 6. 顯示各帳戶餘額
cols = st.columns(3)
for i, (bank, bal) in enumerate(balances.items()):
    cols[i % 3].write(f"**{bank}**: ${bal:,.0f}")

st.divider()

# 7. 修改/刪除紀錄功能
st.subheader("📝 歷史紀錄與管理")
if not st.session_state.transactions:
    st.info("目前還沒有任何交易紀錄喔！")
else:
    # 建立一個帶有索引的 DataFrame 方便管理
    display_df = pd.DataFrame(st.session_state.transactions)
    
    for idx, row in display_df.iterrows():
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        c1.write(f"從: {row['From']}")
        c2.write(f"到: {row['To']}")
        c3.write(f"${row['Amount']:,.0f}")
        # 刪除按鈕
        if c4.button("刪除", key=f"del_{idx}"):
            st.session_state.transactions.pop(idx)
            st.rerun()
