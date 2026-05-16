import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 妳的 9 個帳戶初始資金
initial_balance = {
    "現金": 1300, "中國信託": 546, "Paypal": 33345, 
    "Linebank-活存": 1312, "Linebank-口袋": 33000, 
    "玉山銀行": 0, "台新銀行": 252, "國泰世華": 1015, 
    "元大銀行": 1606, "星展銀行": 0
}

# 緊急備用金目標
EMERGENCY_FUND_TARGET = 150000

# 2. 建立 Google Sheets 連結
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取現有紀錄
def get_data():
    return conn.read(ttl="0")

df_tx = get_data()

st.title("💰 雲端同步記帳 App V5.0")

# --- A. 快速新增交易區 ---
with st.container():
    with st.form("transaction_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            out_acc = st.selectbox("轉出", ["(無)"] + list(initial_balance.keys()))
        with c2:
            in_acc = st.selectbox("轉入", ["(無)"] + list(initial_balance.keys()))
        with c3:
            amount = st.number_input("金額", min_value=0, step=10)
        
        note = st.text_input("📝 備註 (例如：Haruka 車票)", "")
        
        if st.form_submit_button("🚀 永久存入雲端"):
            new_data = pd.DataFrame([{
                "From": out_acc, "To": in_acc, "Amount": amount, "Note": note
            }])
            # 將新資料加到舊資料後面並更新雲端表格
            updated_df = pd.concat([df_tx, new_data], ignore_index=True)
            conn.update(data=updated_df)
            st.success("資料已成功寫入 Google Sheets！")
            st.rerun()

st.divider()

# --- B. 緊急備用金進度 (僅計算口袋帳戶) ---
lb_pocket = initial_balance["Linebank-口袋"]
if not df_tx.empty:
    lb_pocket += (df_tx[df_tx['To'] == "Linebank-口袋"]['Amount'].astype(float).sum() - 
                  df_tx[df_tx['From'] == "Linebank-口袋"]['Amount'].astype(float).sum())

progress_ratio = min(lb_pocket / EMERGENCY_FUND_TARGET, 1.0)
remaining = EMERGENCY_FUND_TARGET - lb_pocket

st.write(f"🚨 **口袋備用金進度: {progress_ratio*100:.1f}%**")
st.progress(progress_ratio)
st.write(f"目前累積: ${lb_pocket:,.0f} | 距離 15 萬目標還差: ${max(0, remaining):,.0f}")

st.divider()

# --- C. 財務總覽與各帳戶餘額 (計算邏輯) ---
reserve_amount = st.sidebar.number_input("預留總金額", min_value=0, value=0)
balances = {}
bank_total = 0
for bank, initial in initial_balance.items():
    curr = initial
    if not df_tx.empty:
        curr += (df_tx[df_tx['To'] == bank]['Amount'].astype(float).sum() - 
                 df_tx[df_tx['From'] == bank]['Amount'].astype(float).sum())
    balances[bank] = curr
    bank_total += curr

net_assets = bank_total - reserve_amount

m1, m2, m3 = st.columns(3)
m1.metric("總額", f"${bank_total:,.0f}")
m2.metric("預留", f"-${reserve_amount:,.0f}")
m3.metric("可用", f"${net_assets:,.0f}")

st.divider()

# --- D. 歷史紀錄 ---
st.subheader("📝 雲端歷史紀錄")
if df_tx.empty:
    st.info("尚無雲端紀錄。")
else:
    # 顯示最近 10 筆
    for idx, row in df_tx.iloc[::-1].iterrows():
        r1, r2, r3 = st.columns([3, 2, 5])
        r1.write(f"{row['From']}➡️{row['To']}")
        r2.write(f"${row['Amount']:,.0f}")
        r3.write(f"💬 {row['Note']}")
