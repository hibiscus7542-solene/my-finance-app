import streamlit as st
import pandas as pd

# 1. 妳的 9 個帳戶初始資金
initial_balance = {
    "現金": 1300, "中國信託": 546, "Paypal": 33345, 
    "Linebank": 14392, "玉山銀行": 0, "台新銀行": 252, 
    "國泰世華": 1015, "元大銀行": 1606, "星展銀行": 0
}

# 信用卡預留金設定 (妳可以隨時修改這裡的數字)
credit_card_debts = {
    "國泰世華": 500,  # 假設目前信用卡費需預留 500
    "星展銀行": 0     # 假設目前信用卡費 0
}

# 2. 初始化交易紀錄
if 'transactions' not in st.session_state:
    st.session_state.transactions = []

st.title("💰 個人多帳戶管理 App V3")

# 3. 新增紀錄功能 (含備註)
with st.form("transaction_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        out_acc = st.selectbox("轉出帳戶", ["(無)"] + list(initial_balance.keys()))
    with col2:
        in_acc = st.selectbox("轉入帳戶", ["(無)"] + list(initial_balance.keys()))
    with col3:
        amount = st.number_input("金額", min_value=0)
    
    note = st.text_input("📝 備註 (例如: 買拉麵、付房租...)", "")
    
    if st.form_submit_button("新增紀錄"):
        st.session_state.transactions.append({
            "From": out_acc, 
            "To": in_acc, 
            "Amount": amount,
            "Note": note
        })
        st.rerun()

# 4. 計算邏輯
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

# 5. 顯示總資產
st.metric(label="📊 總資產淨值 (TWD)", value=f"${total_assets:,.0f}")

st.divider()

# 6. 顯示各帳戶餘額與信用卡提醒
st.subheader("🏦 帳戶可用餘額 (扣除預留金)")
cols = st.columns(3)
for i, (bank, bal) in enumerate(balances.items()):
    with cols[i % 3]:
        debt = credit_card_debts.get(bank, 0)
        available = bal - debt
        
        st.write(f"**{bank}**")
        st.write(f"帳面: ${bal:,.0f}")
        
        if debt > 0:
            st.caption(f"⚠️ 預留卡費: -{debt}")
            
        if available < 0:
            st.error(f"可用: ${available:,.0f}") # 負數顯示紅色
        else:
            st.success(f"可用: ${available:,.0f}") # 正數顯示綠色

st.divider()

# 7. 修改/刪除紀錄功能 (含備註顯示)
st.subheader("📝 歷史紀錄")
if not st.session_state.transactions:
    st.info("目前還沒有交易紀錄。")
else:
    for idx, row in enumerate(st.session_state.transactions):
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        c1.write(f"{row['From']} ➡️ {row['To']}")
        c2.write(f"${row['Amount']:,.0f}")
        c3.write(f"💬 {row['Note']}") # 顯示備註
        if c4.button("❌", key=f"del_{idx}"):
            st.session_state.transactions.pop(idx)
            st.rerun()
