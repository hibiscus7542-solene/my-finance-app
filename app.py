import streamlit as st
import pandas as pd

# 1. 妳的 9 個帳戶初始資金
initial_balance = {
    "現金": 1300, "中國信託": 546, "Paypal": 33345, 
    "Linebank": 14392, "玉山銀行": 0, "台新銀行": 252, 
    "國泰世華": 1015, "元大銀行": 1606, "星展銀行": 0
}

# 2. 初始化交易紀錄
if 'transactions' not in st.session_state:
    st.session_state.transactions = []

# 初始化「正在編輯哪一筆」的狀態
if 'editing_idx' not in st.session_state:
    st.session_state.editing_idx = None

st.title("💰 專業多帳戶管理系統 V4.2")

# --- A. 最上方：新增紀錄區 ---
with st.container():
    st.subheader("➕ 新增交易")
    with st.form("transaction_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            out_acc = st.selectbox("轉出帳戶", ["(無)"] + list(initial_balance.keys()))
        with c2:
            in_acc = st.selectbox("轉入帳戶", ["(無)"] + list(initial_balance.keys()))
        with c3:
            amount = st.number_input("金額", min_value=0, step=10)
        
        note = st.text_input("📝 交易備註", "")
        
        if st.form_submit_button("🚀 儲存紀錄"):
            st.session_state.transactions.append({
                "From": out_acc, "To": in_acc, "Amount": amount, "Note": note
            })
            st.rerun()

st.divider()

# --- B. 預留金設定區 ---
st.subheader("🛡️ 支出預留 (卡費/房租)")
col_debt1, col_debt2 = st.columns([1, 2])
with col_debt1:
    reserve_amount = st.number_input("預留總金額", min_value=0, value=0, step=100)
with col_debt2:
    reserve_note = st.text_input("備註說明", placeholder="預留給：國泰卡費")

st.divider()

# 3. 計算邏輯 (核心)
df_tx = pd.DataFrame(st.session_state.transactions)
bank_total = sum(initial_balance.values())
if not df_tx.empty:
    # 這裡簡化邏輯：總資產 = 初始總和 + (所有無來源轉入 - 所有無目的地轉出)
    # 但為了精確，我們維持原本的各帳戶計算加總
    balances = {}
    bank_total = 0
    for bank, initial in initial_balance.items():
        current = initial
        in_sum = df_tx[df_tx['To'] == bank]['Amount'].sum()
        out_sum = df_tx[df_tx['From'] == bank]['Amount'].sum()
        current += (in_sum - out_sum)
        balances[bank] = current
        bank_total += current
else:
    balances = initial_balance

net_assets = bank_total - reserve_amount

# --- C. 資產總額儀表板 ---
m1, m2, m3 = st.columns(3)
m1.metric("銀行帳面總額", f"${bank_total:,.0f}")
m2.metric("預留支出項目", f"-${reserve_amount:,.0f}", delta_color="inverse")
m3.metric("可動用淨資產", f"${net_assets:,.0f}")

st.divider()

# --- D. 各帳戶詳細清單 ---
st.write("📂 **各帳戶詳細餘額**")
cols = st.columns(3)
for i, (bank, bal) in enumerate(balances.items()):
    cols[i % 3].info(f"**{bank}**\n\n${bal:,.0f}")

st.divider()

# --- E. 歷史紀錄 (含編輯功能) ---
st.subheader("📝 歷史紀錄")
if not st.session_state.transactions:
    st.info("尚未有交易紀錄。")
else:
    # 讓最新紀錄在最上面
    for idx, row in enumerate(reversed(st.session_state.transactions)):
        real_idx = len(st.session_state.transactions) - 1 - idx
        
        with st.container():
            # 判斷這筆是否正在編輯
            if st.session_state.editing_idx == real_idx:
                # 編輯模式介面
                with st.expander("📝 編輯備註中...", expanded=True):
                    new_note = st.text_input("修改備註", value=row.get('Note', ''), key=f"edit_note_{real_idx}")
                    col_save, col_cancel = st.columns(2)
                    if col_save.button("✅ 儲存修改", key=f"save_{real_idx}"):
                        st.session_state.transactions[real_idx]['Note'] = new_note
                        st.session_state.editing_idx = None
                        st.rerun()
                    if col_cancel.button("❌ 取消", key=f"cancel_{real_idx}"):
                        st.session_state.editing_idx = None
                        st.rerun()
            else:
                # 一般顯示模式介面
                r1, r2, r3, r4, r5 = st.columns([2.5, 2, 3.5, 1, 1])
                r1.write(f"**{row['From']}** ➡️ **{row['To']}**")
                r2.write(f"${row['Amount']:,.0f}")
                r3.write(f"💬 {row.get('Note', '')}")
                
                # 編輯按鈕
                if r4.button("✏️", key=f"edit_btn_{real_idx}"):
                    st.session_state.editing_idx = real_idx
                    st.rerun()
                
                # 刪除按鈕
                if r5.button("🗑️", key=f"del_{real_idx}"):
                    st.session_state.transactions.pop(real_idx)
                    st.rerun()
