import streamlit as st
import requests
import pandas as pd
import time

# --- 頁面配置 ---
st.set_page_config(page_title="以太坊地址風險監控", layout="wide")

# --- 從 Streamlit Secrets 讀取 API Key (部署後在後台設定) ---
# 如果本地測試找不到 secrets，則使用預設值
ETHERSCAN_API_KEY = st.secrets.get("ETHERSCAN_API_KEY", "RGJWZ5TEK21HXBKIIYNZYC5GPSSHG1ZS9Y")

def get_tx_history(address):
    """取得地址最近的交易紀錄"""
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=20&sort=desc&apikey={ETHERSCAN_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if data["status"] == "1":
            return data["result"]
        return []
    except Exception as e:
        st.error(f"連線錯誤: {e}")
        return []

def analyze_risk(address, tx_list):
    """簡單的風險分析邏輯"""
    risk_score = 0
    reasons = []
    
    if not tx_list:
        return "未知/無交易", "無法分析（無歷史資料）", "gray"
    
    # 範例邏輯：交易頻率過高或與已知風險地址互動（此處為示範）
    if len(tx_list) > 15:
        risk_score += 40
        reasons.append("交易頻繁 (近期超過 15 筆)")
    
    # 假設某些特定地址是黑名單 (範例地址)
    high_risk_targets = ["0x722122df12d4e14e13ac3b6895a86e84145b6967"]
    for tx in tx_list:
        if tx["to"].lower() in high_risk_targets:
            risk_score += 60
            reasons.append("曾與已知高風險合約互動")
            break

    if risk_score >= 60:
        return "高風險", " / ".join(reasons), "red"
    elif risk_score >= 30:
        return "中風險", " / ".join(reasons), "orange"
    else:
        return "低風險", "交易行為正常", "green"

# --- 介面設計 ---
st.title("🛡️ 以太坊地址安全監測系統")
st.markdown("輸入以太坊錢包地址，即時分析其交易風險與行為特徵。")

with st.sidebar:
    st.header("參數設定")
    st.info("目前使用 Etherscan API 進行資料抓取")
    st.write("---")
    st.caption("v1.0.0 Stable")

address_input = st.text_input("請輸入以太坊地址 (0x...)", placeholder="0x722122dF12D4e14e13Ac3b6895a86e84145b6967")

if address_input:
    if len(address_input) == 42 and address_input.startswith("0x"):
        with st.spinner('正在從區塊鏈抓取資料...'):
            txs = get_tx_history(address_input)
            label, reason, color = analyze_risk(address_input, txs)
            
            # 顯示結果卡片
            st.subheader("分析摘要")
            col1, col2, col3 = st.columns(3)
            col1.metric("風險等級", label)
            col2.metric("交易總數 (樣本)", len(txs))
            col3.markdown(f"**診斷結果：** <span style='color:{color}'>{reason}</span>", unsafe_allow_html=True)

            if txs:
                st.write("---")
                st.subheader("最近交易明細")
                df = pd.DataFrame(txs)[['blockNumber', 'timeStamp', 'from', 'to', 'value', 'gasUsed']]
                # 轉換時間戳
                df['timeStamp'] = pd.to_datetime(df['timeStamp'].astype(int), unit='s')
                st.dataframe(df, use_container_width=True)
    else:
        st.error("❌ 請輸入正確的以太坊地址格式")