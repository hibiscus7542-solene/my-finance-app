import streamlit as st
import pandas as pd

# 1. 妳的 9 個帳戶初始資金
initial_balance = {
    "現金": 1300, "中國信託": 546, "Paypal": 33345, 
    "Linebank-活存": 1312, "Linebank-口袋": 33000, 
    "玉山銀行": 0, "台新銀行": 252, "國泰世華": 1015, 
    "元大銀行": 1606, "星展銀行": 0
}

# 緊急備用金目標 (僅針對口袋帳戶)
EMERGENCY_FUND_TARGET = 150000

# 2. 初始化交易紀錄
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
if 'editing_idx' not in st.session_state:
    st.session_state.editing_idx = None

st.title("💰 隨手記帳 App V4.6")

# --- A. 【最優先】快速新增交易區 ---
with st.container():
    with st.form("transaction_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            out_acc = st.selectbox("轉出", ["(無)"] + list(initial_balance.keys()))
        with c2:
            in_acc = st.selectbox("轉入", ["(無)"] + list(initial_balance.keys()))
        with c3:
            amount = st.number_input("金額", min_value=0, step=10)
        
        note = st.text_input("📝 備註 (拉麵、交通...)", "")
        
        if st.form_submit_button("🚀 儲存紀錄"):
            st.session_state.transactions.append({
                "From": out_acc, "To": in_acc, "Amount": amount, "Note": note
            })
            st.rerun()

st.divider()

# --- B. 精簡版：緊急備用金進度 (僅計算口袋帳戶) ---
df_tx = pd.DataFrame(st.session_state.transactions)
lb_pocket = initial_balance["Linebank-口袋"]

# 邏輯修正：只計算流入/流出「Linebank-口袋」的交易
if not df_tx.empty:
    lb_pocket += (df_tx[df_tx['To'] == "Linebank-口袋"]['Amount'].sum() - 
                  df_tx[df_tx['From'] == "Linebank-口袋"]['Amount'].sum())

progress_ratio = min(lb_pocket / EMERGENCY_FUND_TARGET, 1.0)
remaining = EMERGENCY_FUND_TARGET - lb_pocket

st.write(f"🚨 **口袋備用金進度: {progress_ratio*100:.1f}%**")
st.progress(progress_ratio)
st.caption(f"目前累積: ${lb_pocket:,.0f} | 距離 15 萬目標還差: **${max(0, remaining):,.0f}**")

st.divider()

# --- C. 財務總覽與預留金 ---
reserve_amount = st.sidebar.number_input("預留總金額 (卡費等)", min_value=0, value=0, step=100)
reserve_note = st.sidebar.text_input("預留項目說明", placeholder="例如：國泰卡費")

balances = {}
bank_total = 0
for bank, initial in initial_balance.items():
    curr = initial
    if not df_tx.empty:
        curr += (df_tx[df_tx['To'] == bank]['Amount'].sum() - 
                 df_tx[df_tx['From'] == bank]['Amount'].sum())
    balances[bank] = curr
    bank_total += curr

net_assets = bank_total - reserve_amount

m1, m2, m3 = st.columns(3)
m1.metric("總額", f"${bank_total:,.0f}")
m2.metric("預留", f"-${reserve_amount:,.0f}")
m3.metric("可用", f"${net_assets:,.0f}")

st.divider()

# --- D. 各帳戶詳細清單 (摺疊顯示) ---
with st.expander("📂 查看 9 個帳戶詳細餘額", expanded=False):
    cols = st.columns(3)
    for i, (bank, bal) in enumerate(balances.items()):
        cols[i % 3].write(f"**{bank}**")
        cols[i % 3].write(f"${bal:,.0f}")

st.divider()

# --- E. 歷史紀錄 (最新在上) ---
st.subheader("📝 歷史紀錄")
if not st.session_state.transactions:
    st.info("尚無紀錄。")
else:
    for idx, row in enumerate(reversed(st.session_state.transactions)):
        real_idx = len(st.session_state.transactions) - 1 - idx
        with st.container():
            if st.session_state.editing_idx == real_idx:
                new_note = st.text_input("修改備註", value=row.get('Note', ''), key=f"edit_{real_idx}")
                if st.button("✅ 儲存", key=f"save_{real_idx}"):
                    st.session_state.transactions[real_idx]['Note'] = new_note
                    st.session_state.editing_idx = None
                    st.rerun()
