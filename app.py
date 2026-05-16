import streamlit as st
import pandas as pd

# 1. 妳的 9 個帳戶初始資金 (這裡固定放銀行存款即可)
initial_balance = {
    "現金": 1300, "中國信託": 546, "Paypal": 33345, 
    "Linebank": 14392, "玉山銀行": 0, "台新銀行": 252, 
    "國泰世華": 1015, "元大銀行": 1606, "星展銀行": 0
}

# 2. 初始化交易紀錄
if 'transactions' not in st.session_state:
    st.session_state.transactions = []

st.title("💰 專業多帳戶管理系統 V4")

# --- 新增：左側或上方的預留金設定區 ---
st.subheader("🛡️ 預留金設定 (卡費/固定支出)")
col_debt1, col_debt2 = st.columns(2)
with col_debt1:
    reserve_amount = st.number_input("請輸入總預留金額 (卡費等)", min_value=0, value=0, step=100)
with col_debt2:
    reserve_note = st.text_input("預留項目備註", placeholder="例如：國泰卡費+房租")

st.divider()

# 3. 新增紀錄功能
with st.expander("➕ 新增交易紀錄", expanded=False):
    with st.form("transaction_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            out_acc = st.selectbox("轉出帳戶", ["(無)"] + list(initial_balance.keys()))
        with c2:
            in_acc = st.selectbox("轉入帳戶", ["(無)"] + list(initial_balance.keys()))
        with c3:
            amount = st.number_input("金額", min_value=0)
        
        note = st.text_input("📝 交易備註", "")
        
        if st.form_submit_button("確認新增"):
            st.session_state.transactions.append({
                "From": out_acc, "To": in_acc, "Amount": amount, "Note": note
            })
            st.rerun()

# 4. 計算邏輯
df_tx = pd.DataFrame(st.session_state.transactions)
balances = {}
bank_total = 0

for bank, initial in initial_balance.items():
    current = initial
    if not df_tx.empty:
        in_sum = df_tx[df_tx['To'] == bank]['Amount'].sum()
        out_sum = df_tx[df_tx['From'] == bank]['Amount'].sum()
        current += (in_sum - out_sum)
    balances[bank] = current
    bank_total += current

# 計算扣除預留金後的淨資產
net_assets = bank_total - reserve_amount

# 5. 總額顯示區
st.subheader("📊 資產概況")
m1, m2, m3 = st.columns(3)
m1.metric("銀行總額", f"${bank_total:,.0f}")
m2.metric("預留支出", f"-${reserve_amount:,.0f}", delta_color="inverse")
m3.metric("可動用淨資產", f"${net_assets:,.0f}")

st.divider()

# 6. 各帳戶清單
st.write("📂 **各帳戶詳細餘額**")
cols = st.columns(3)
for i, (bank, bal) in enumerate(balances.items()):
    cols[i % 3].info(f"**{bank}**\n\n${bal:,.0f}")

st.divider()

# 7. 歷史紀錄
st.subheader("📝 歷史紀錄")
if not st.session_state.transactions:
    st.info("尚未有交易紀錄。")
else:
    for idx, row in enumerate(reversed(st.session_state.transactions)):
        # 反轉順序讓最新的在上面
        real_idx = len(st.session_state.transactions) - 1 - idx
        with st.container():
            r1, r2, r3, r4 = st.columns([3, 2, 4, 1])
            r1.write(f"**{row['From']}** ➡️ **{row['To']}**")
            r2.write(f"${row['Amount']:,.0f}")
            r3.write(f"💬 {row.get('Note', '')}")
            if r4.button("🗑️", key=f"del_{real_idx}"):
                st.session_state.transactions.pop(real_idx)
                st.rerun()
