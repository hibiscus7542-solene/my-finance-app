import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. 妳的帳戶初始資金
initial_balance = {
    "現金": 1300, "中國信託": 546, "Paypal": 33345, 
    "Linebank-活存": 1312, "Linebank-口袋": 33000, 
    "玉山銀行": 0, "台新銀行": 252, "國泰世華": 1015, 
    "元大銀行": 1606, "星展銀行": 0
}

# 2. 連結設定 (直接從 Secrets 抓網址)
url = st.secrets["spreadsheet"]
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        # 讀取現有資料
        return conn.read(spreadsheet=url, ttl=0)
    except:
        return pd.DataFrame(columns=["From", "To", "Amount", "Note"])

df_tx = get_data()

st.title("💰 雲端記帳本 (簡約穩定版)")

# --- A. 快速新增交易 ---
with st.container():
    with st.form("transaction_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            out_acc = st.selectbox("轉出", ["(無)"] + list(initial_balance.keys()))
        with c2:
            in_acc = st.selectbox("轉入", ["(無)"] + list(initial_balance.keys()))
        with c3:
            amount = st.number_input("金額", min_value=0, step=10)
        
        note = st.text_input("📝 備註", "")
        
        if st.form_submit_button("🚀 存入雲端"):
            new_row = pd.DataFrame([{"From": out_acc, "To": in_acc, "Amount": amount, "Note": note}])
            updated_df = pd.concat([df_tx, new_row], ignore_index=True)
            # 使用最單純的更新方式
            conn.update(spreadsheet=url, data=updated_df)
            st.success("成功存入！")
            st.rerun()

# --- B. 進度條與餘額計算 (與之前邏輯一致) ---
lb_pocket = initial_balance["Linebank-口袋"]
if not df_tx.empty:
    df_tx["Amount"] = pd.to_numeric(df_tx["Amount"], errors='coerce').fillna(0)
    lb_pocket += (df_tx[df_tx['To'] == "Linebank-口袋"]['Amount'].sum() - 
                  df_tx[df_tx['From'] == "Linebank-口袋"]['Amount'].sum())

st.write(f"🚨 **口袋備用金進度: {min(100, lb_pocket/150000*100):.1f}%**")
st.progress(min(1.0, lb_pocket/150000))
st.write(f"目前累積: ${lb_pocket:,.0f} | 離 15 萬還差: ${max(0, 150000-lb_pocket):,.0f}")

st.divider()

# --- C. 歷史紀錄 ---
st.subheader("📝 歷史紀錄")
if not df_tx.empty:
    for idx, row in df_tx.iloc[::-1].head(10).iterrows():
        c1, c2, c3 = st.columns([3, 2, 4])
        c1.write(f"{row['From']} ➡️ {row['To']}")
        c2.write(f"${row['Amount']:,.0f}")
        c3.write(f"💬 {row['Note']}")
