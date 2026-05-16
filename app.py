import streamlit as st
import pandas as pd

# 1. 妳的 9 個帳戶初始資金 (已更新 Line Bank 金額)
initial_balance = {
    "現金": 1300, "中國信託": 546, "Paypal": 33345, 
    "Linebank-活存": 1312, "Linebank-口袋": 33000, 
    "玉山銀行": 0, "台新銀行": 252, "國泰世華": 1015, 
    "元大銀行": 1606, "星展銀行": 0
}

# 緊急備用金目標
EMERGENCY_FUND_TARGET = 150000

# 2. 初始化交易紀錄
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
if 'editing_idx' not in st.session_state:
    st.session_state.editing_idx = None

st.title("💰 專業多帳戶管理系統 V4.4")

# --- A. 視覺化：緊急備用金進度儀表板 ---
# 計算目前紀錄後的 Line Bank 金額
df_tx = pd.DataFrame(st.session_state.transactions)
lb_savings = initial_balance["Linebank-活存"]
lb_pocket = initial_balance["Linebank-口袋"]

if not df_tx.empty:
    lb_savings += (df_tx[df_tx['To'] == "Linebank-活存"]['Amount'].sum() - df_tx[df_tx['From'] == "Linebank-活存"]['Amount'].sum())
    lb_pocket += (df_tx[df_tx['To'] == "Linebank-口袋"]['Amount'].sum() - df_tx[df_tx['From'] == "Linebank-口袋"]['Amount'].sum())

total_emergency_fund = lb_savings + lb_pocket
progress_ratio = min(total_emergency_fund / EMERGENCY_FUND_TARGET, 1.0)

st.subheader("🚨 緊急備用金達標進度")
# 使用進度條與百分比顯示
st.progress(progress_ratio)
col_prog1, col_prog2 = st.columns([3, 1])
col_prog1.write(f"目前總累積: **${total_emergency_fund:,.0f}** / 目標: **${EMERGENCY_FUND_TARGET:,.0f}**")
col_prog2.write(f"**{progress_ratio*100:.1f}%**")

# Line Bank 細節區
with st.container():
    c_lb1, c_lb2 = st.columns(2)
    c_lb1.metric("Linebank 活存", f"${lb_savings:,.0f}")
    c_lb2.metric("Linebank 口袋", f"${lb_pocket:,.0f}")

st.divider()

# --- B. 快速新增交易區 ---
with st.container():
    st.subheader("➕ 快速新增交易")
    with st.form("transaction_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            out_acc = st.selectbox("轉出帳戶", ["(無)"] + list(initial_balance.keys()))
        with c2:
            in_acc = st.selectbox("轉入帳戶", ["(無)"] + list(initial_balance.keys()))
        with c3:
            amount = st.number_input("金額", min_value=0, step=10)
        
        note = st.text_input("📝 交易備註", "")
        
        if st.form_submit_button("🚀 點我儲存紀錄"):
            st.session_state.transactions.append({
                "From": out_acc, "To": in_acc, "Amount": amount, "Note": note
            })
            st.rerun()

st.divider()

# --- C. 財務總覽與預留金 ---
# 將預留金設定放在側邊欄，避免干擾主畫面
reserve_amount = st.sidebar.number_input("預留總金額 (卡費等)", min_value=0, value=0, step=100)
reserve_note = st.sidebar.text_input("預留項目說明", placeholder="例如：國泰卡費")

balances = {}
bank_total = 0
for bank, initial in initial_balance.items():
    curr = initial
    if not df_tx.empty:
        curr += (df_tx[df_tx['To'] == bank]['Amount'].sum() - df_tx[df_tx['From'] == bank]['Amount'].sum())
    balances[bank] = curr
    bank_total += curr

net_assets = bank_total - reserve_amount

st.subheader("📊 財務水位總覽")
m1, m2, m3 = st.columns(3)
m1.metric("銀行帳面總額", f"${bank_total:,.0f}")
m2.metric("預留支出", f"-${reserve_amount:,.0f}", delta_color="inverse")
m3.metric("可動用淨資產", f"${net_assets:,.0f}")

st.divider()

# --- D. 各帳戶詳細清單 ---
st.write("📂 **各帳戶詳細餘額**")
cols = st.columns(3)
for i, (bank, bal) in enumerate(balances.items()):
    cols[i % 3].info(f"**{bank}**\n\n${bal:,.0f}")

st.divider()

# --- E. 歷史紀錄 (含編輯與刪除) ---
st.subheader("📝 歷史紀錄")
if not st.session_state.transactions:
    st.info("尚未有交易紀錄。")
else:
    for idx, row in enumerate(reversed(st.session_state.transactions)):
        real_idx = len(st.session_state.transactions) - 1 - idx
        with st.container():
            if st.session_state.editing_idx == real_idx:
                new_note = st.text_input("修改備註", value=row.get('Note', ''), key=f"edit_note_{real_idx}")
                if st.button("✅ 儲存修改", key=f"save_{real_idx}"):
                    st.session_state.transactions[real_idx]['Note'] = new_note
                    st.session_state.editing_idx = None
                    st.rerun()
            else:
                r1, r2, r3, r4, r5 = st.columns([2.5, 2, 3.5, 1, 1])
                r1.write(f"**{row['From']}** ➡️ **{row['To']}**")
                r2.write(f"${row['Amount']:,.0f}")
                r3.write(f"💬 {row.get('Note', '')}")
                if r4.button("✏️", key=f"edit_btn_{real_idx}"):
                    st.session_state.editing_idx = real_idx
                    st.rerun()
                if r5.button("🗑️", key=f"del_btn_{real_idx}"):
                    st.session_state.transactions.pop(real_idx)
                    st.rerun()
