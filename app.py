import streamlit as st
import pandas as pd
import requests

# 1. 妳的帳戶初始資金
initial_balance = {
    "現金": 1300, "中國信託": 546, "Paypal": 14, 
    "Linebank-活存": 1312, "Linebank-口袋": 33000, 
    "玉山銀行": 15827, "台新銀行": 252, "國泰世華": 1015, 
    "元大銀行": 1606, "星展銀行": 0
}

# --- 這裡放入妳剛剛拿到的 Google 腳本網址 ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz78lUQ6g2rFHB12E8laaE4PjvVYGZjTYawYz0_K6WctZSjHYPiFZgY665Ee67Xz64/exec"

# --- 這裡放入妳 Google 表格的 ID (就是網址中 /d/ 後面那一串) ---
# 格式範例：https://docs.google.com/spreadsheets/d/妳的ID/gviz/tq?tqx=out:csv
# 請檢查妳的 ID 並替換下面這行
SHEET_ID = "1Bwcg3ABnVl-cyqKK-jNagqVGqM_Jl3KhFsyV11YZ2_s" # <--- 請把這串換成妳真正的表格 ID
SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# 2. 讀取資料函數
def get_data():
    try:
        # 直接讀取 Google 表格發布的 CSV
        return pd.read_csv(SHEET_CSV_URL)
    except:
        return pd.DataFrame(columns=["From", "To", "Amount", "Note"])

df_tx = get_data()

st.title("🚀 記帳系統 V5.1")

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
        
        if st.form_submit_button("💾 儲存"):
            payload = {
                "From": out_acc, 
                "To": in_acc, 
                "Amount": amount, 
                "Note": note
            }
            # 使用 POST 方法把資料推給 Google Apps Script
            try:
                response = requests.post(SCRIPT_URL, json=payload)
                if response.status_code == 200:
                    st.success("🎉 雲端儲存成功！")
                    st.rerun()
                else:
                    st.error(f"儲存失敗，錯誤碼：{response.status_code}")
            except Exception as e:
                st.error(f"連線出錯：{e}")

st.divider()

# --- B. 緊急備用金進度 ---
# (計算邏輯與之前一致)
lb_pocket = initial_balance["Linebank-口袋"]
if not df_tx.empty:
    # 確保欄位名稱正確且為數字
    if "Amount" in df_tx.columns:
        df_tx["Amount"] = pd.to_numeric(df_tx["Amount"], errors='coerce').fillna(0)
        lb_pocket += (df_tx[df_tx['To'] == "Linebank-口袋"]['Amount'].sum() - 
                      df_tx[df_tx['From'] == "Linebank-口袋"]['Amount'].sum())

progress_ratio = min(lb_pocket / 150000, 1.0)
st.write(f"🚨 **口袋備用金進度: {progress_ratio*100:.1f}%**")
st.progress(progress_ratio)
st.write(f"目前累積: ${lb_pocket:,.0f} | 距離目標還差: ${max(0, 150000-lb_pocket):,.0f}")

st.divider()

# --- C. 財務概況 (計算各帳戶) ---
balances = {}
bank_total = 0
for bank, initial in initial_balance.items():
    curr = initial
    if not df_tx.empty and "Amount" in df_tx.columns:
        in_s = df_tx[df_tx['To'] == bank]['Amount'].sum()
        out_s = df_tx[df_tx['From'] == bank]['Amount'].sum()
        curr += (in_s - out_s)
    balances[bank] = curr
    bank_total += curr

m1, m2 = st.columns(2)
m1.metric("銀行總額", f"${bank_total:,.0f}")
m2.metric("可動用淨資產", f"${bank_total:,.0f}") # 這裡可依需求再扣除預留金

st.divider()

# --- D. 雲端紀錄列表 ---
st.subheader("📝 雲端歷史紀錄")
if df_tx.empty:
    st.info("雲端目前沒有紀錄。")
else:
    # 顯示最後 10 筆
    for idx, row in df_tx.iloc[::-1].head(10).iterrows():
        c1, c2, c3 = st.columns([3, 2, 4])
        c1.write(f"{row['From']} ➡️ {row['To']}")
        c2.write(f"${row['Amount']:,.0f}")
        c3.write(f"💬 {row.get('Note', '')}")
