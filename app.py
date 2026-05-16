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

# 2. 建立 Google Sheets 連結 (使用安全通道)
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取雲端資料函數
def get_data():
    try:
        # ttl=0 代表每次都抓最新的，不使用舊的快取資料
        return conn.read(ttl=0)
    except Exception as e:
        # 如果雲端是空的或讀取失敗，回傳一個空的欄位表格
        return pd.DataFrame(columns=["From", "To", "Amount", "Note"])

# 執行讀取
df_tx = get_data()

df_tx = get_data()

st.title("💰 記帳 App V5.0")

# --- A. 【最上方】快速新增交易區 ---
with st.container():
    with st.form("transaction_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            out_acc = st.selectbox("轉出", ["(無)"] + list(initial_balance.keys()))
        with c2:
            in_acc = st.selectbox("轉入", ["(無)"] + list(initial_balance.keys()))
        with c3:
            amount = st.number_input("金額", min_value=0, step=10)
        
        note = st.text_input("📝 備註 (薪資、交通...)", "")
        
        if st.form_submit_button("🚀 儲存"):
            new_data = pd.DataFrame([{
                "From": out_acc, "To": in_acc, "Amount": amount, "Note": note
            }])
            updated_df = pd.concat([df_tx, new_data], ignore_index=True)
            conn.update(data=updated_df)
            st.success("成功存入 Google Sheets！")
            st.rerun()

st.divider()

# --- B. 精簡版：緊急備用金進度 (修正字體與符號問題) ---
lb_pocket = initial_balance["Linebank-口袋"]
if not df_tx.empty:
    # 確保金額是數字格式
    df_tx["Amount"] = pd.to_numeric(df_tx["Amount"], errors='coerce').fillna(0)
    lb_pocket += (df_tx[df_tx['To'] == "Linebank-口袋"]['Amount'].sum() - 
                  df_tx[df_tx['From'] == "Linebank-口袋"]['Amount'].sum())

progress_ratio = min(lb_pocket / EMERGENCY_FUND_TARGET, 1.0)
remaining = max(0, EMERGENCY_FUND_TARGET - lb_pocket)

st.write(f"🚨 **口袋備用金進度: {progress_ratio*100:.1f}%**")
st.progress(progress_ratio)

# 修正：直接使用純文字，不加 ** 避免解析錯誤
st.write(f"目前累積: ${lb_pocket:,.0f} | 距離 15 萬目標還差: ${remaining:,.0f}")

st.divider()

# --- C. 財務總覽與預留金 ---
reserve_amount = st.sidebar.number_input("預留總金額 (卡費等)", min_value=0, value=0, step=100)

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
with st.expander("📂 查看各帳戶餘額", expanded=False):
    cols = st.columns(3)
    for i, (bank, bal) in enumerate(balances.items()):
        cols[i % 3].write(f"**{bank}**")
        cols[i % 3].write(f"${bal:,.0f}")

st.divider()

# --- E. 雲端歷史紀錄 (最新 10 筆) ---
st.subheader("📝 雲端歷史紀錄")
if df_tx.empty:
    st.info("尚未有雲端紀錄，請先嘗試新增一筆！")
else:
    for idx, row in df_tx.iloc[::-1].head(10).iterrows():
        with st.container():
            r1, r2, r3 = st.columns([3, 2, 4])
            r1.write(f"{row['From']} ➡️ {row['To']}")
            r2.write(f"${row['Amount']:,.0f}")
            r3.write(f"💬 {row.get('Note', '')}")
