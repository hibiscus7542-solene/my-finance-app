import streamlit as st
import pandas as pd
import requests

# 1. 妳的帳戶初始資金 (已同步最新餘額)
initial_balance = {
    "現金": 1300, "中國信託": 546, "Paypal": 14, 
    "Linebank-活存": 1312, "Linebank-口袋": 33000, 
    "玉山銀行": 15827, "台新銀行": 252, 
    "國泰世華": 1015, "元大銀行": 1606, "星展銀行": 0
}

# --- 核心設定區 (已更新 SHEET_ID) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxb29SmjNZFpwKOzyeJJOt72zZoPaJmK-O-7D-8fLPUHvJydnkO_kyun5xYrIai1_o/exec"
SHEET_ID = "1Bwcg3ABnVl-cyqKK-jNagqVGqM_Jl3KhFsyV11YZ2_s" 
SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# 初始化狀態
if 'editing_idx' not in st.session_state: st.session_state.editing_idx = None
if 'reserves' not in st.session_state: st.session_state.reserves = []

# 2. 讀取資料
def get_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        if "Amount" in df.columns:
            df["Amount"] = pd.to_numeric(df["Amount"], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame(columns=["From", "To", "Amount", "Note"])

df_tx = get_data()

st.title("💰 財務管理工具 V5.6")

# --- A. 側邊欄：多筆預留金管理 ---
st.sidebar.header("🛡️ 預留金清單")

with st.sidebar.expander("➕ 新增預留項目", expanded=False):
    with st.form("reserve_form", clear_on_submit=True):
        r_name = st.text_input("項目名稱 (如：房租)")
        r_amt = st.number_input("金額", min_value=0, step=100)
        r_note = st.text_input("備註", placeholder="選填")
        if st.form_submit_button("新增預留"):
            if r_name:
                st.session_state.reserves.append({"name": r_name, "amount": r_amt, "note": r_note})
                st.rerun()

total_reserve = 0
if st.session_state.reserves:
    st.sidebar.write("---")
    for i, res in enumerate(st.session_state.reserves):
        with st.sidebar.container():
            c1, c2 = st.columns([4, 1])
            # 這裡讓金額可以直接編輯
            new_amt = c1.number_input(f"{res['name']} ({res['note']})", 
                                      value=int(res['amount']), key=f"res_amt_{i}")
            st.session_state.reserves[i]['amount'] = new_amt
            total_reserve += new_amt
            if c2.button("🗑️", key=f"del_res_{i}"):
                st.session_state.reserves.pop(i)
                st.rerun()

st.sidebar.divider()
st.sidebar.metric("預留金總計", f"${total_reserve:,.0f}")

# --- B. 快速新增交易 ---
with st.container():
    with st.form("transaction_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1: out_acc = st.selectbox("轉出", ["(無)"] + list(initial_balance.keys()))
        with c2: in_acc = st.selectbox("轉入", ["(無)"] + list(initial_balance.keys()))
        with c3: amount = st.number_input("金額", min_value=0, step=10)
        note = st.text_input("📝 備註", "")
        
        if st.form_submit_button("💾 存入 Google 雲端"):
            payload = {"method": "post", "From": out_acc, "To": in_acc, "Amount": amount, "Note": note}
            requests.post(SCRIPT_URL, json=payload)
            st.success("🎉 儲存成功！")
            st.rerun()

st.divider()

# --- C. 緊急備用金進度 ---
lb_pocket = initial_balance["Linebank-口袋"]
if not df_tx.empty and "Amount" in df_tx.columns:
    lb_pocket += (df_tx[df_tx['To'] == "Linebank-口袋"]['Amount'].sum() - 
                  df_tx[df_tx['From'] == "Linebank-口袋"]['Amount'].sum())

progress_ratio = min(lb_pocket / 150000, 1.0)
st.write(f"🚨 **口袋備用金進度: {progress_ratio*100:.1f}%**")
st.progress(progress_ratio)
st.write(f"目前累積: ${lb_pocket:,.0f} | 距離目標還差: ${max(0, 150000-lb_pocket):,.0f}")

st.divider()

# --- D. 財務概況看板 ---
balances = {}
bank_total = 0
for bank, initial in initial_balance.items():
    curr = initial
    if not df_tx.empty and "Amount" in df_tx.columns:
        curr += (df_tx[df_tx['To'] == bank]['Amount'].sum() - df_tx[df_tx['From'] == bank]['Amount'].sum())
    balances[bank] = curr
    bank_total += curr

m1, m2, m3 = st.columns(3)
m1.metric("總資產", f"${bank_total:,.0f}")
m2.metric("預留金", f"-${total_reserve:,.0f}")
m3.metric("可用淨額", f"${bank_total - total_reserve:,.0f}")

with st.expander("📂 各帳戶餘額細節"):
    cols = st.columns(3)
    for i, (bank, bal) in enumerate(balances.items()):
        cols[i % 3].write(f"**{bank}**\n${bal:,.0f}")

st.divider()

# --- E. 雲端歷史紀錄 (編輯/刪除) ---
st.subheader("📝 雲端歷史紀錄")
if df_tx.empty:
    st.info("尚無紀錄")
else:
    for idx, row in df_tx.iloc[::-1].iterrows():
        with st.container():
            if st.session_state.editing_idx == idx:
                new_note = st.text_input("修改備註", value=str(row['Note']), key=f"edit_{idx}")
                c_s, c_c = st.columns(2)
                if c_s.button("✅ 儲存", key=f"save_{idx}"):
                    requests.post(SCRIPT_URL, json={"method": "update", "index": int(idx), "new_note": new_note})
                    st.session_state.editing_idx = None
                    st.rerun()
                if c_c.button("❌ 取消", key=f"cancel_{idx}"):
                    st.session_state.editing_idx = None
                    st.rerun()
            else:
                r1, r2, r3, r4, r5 = st.columns([2.5, 2, 3, 1, 1])
                r1.write(f"{row['From']}➡️{row['To']}")
                r2.write(f"${row['Amount']:,.0f}")
                r3.write(f"💬 {row.get('Note', '')}")
                if r4.button("✏️", key=f"ed_{idx}"):
                    st.session_state.editing_idx = idx
                    st.rerun()
                if r5.button("🗑️", key=f"de_{idx}"):
                    # 發送刪除請求，確保 index 是整數
                    requests.post(SCRIPT_URL, json={"method": "delete", "index": int(idx)})
                    st.rerun()
