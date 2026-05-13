import streamlit as st
import requests
import pandas as pd

# --- Page config ---
st.set_page_config(page_title="Ethereum Address Risk Monitor", layout="wide")

# --- API Key ---
ETHERSCAN_API_KEY = st.secrets.get("ETHERSCAN_API_KEY", "RGJWZ5TEK21HXBKIIYNZYC5GPSSHG1ZS9Y")

ETHERSCAN_BASE = "https://api.etherscan.io/v2/api"

TORNADO_CASH = {"0x722122df12d4e14e13ac3b6895a86e84145b6967"}

def get_tx_history(address):
    """Fetch recent transaction history for an address"""
    try:
        resp = requests.get(ETHERSCAN_BASE, params={
            "chainid": "1",
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 20,
            "sort": "desc",
            "apikey": ETHERSCAN_API_KEY
        }, timeout=15)
        data = resp.json()
        result = data.get("result", [])
        if isinstance(result, list):
            return result
        return []
    except Exception as e:
        st.error(f"Connection error: {e}")
        return []

def analyze_risk(address, tx_list):
    """Risk analysis logic"""
    risk_score = 0
    reasons = []

    if not tx_list:
        return "Unknown", "No transaction history available", "gray"

    if len(tx_list) > 15:
        risk_score += 40
        reasons.append("High transaction frequency (>15 recent transactions)")

    for tx in tx_list:
        if tx.get("to", "").lower() in TORNADO_CASH:
            risk_score += 60
            reasons.append("Direct interaction with Tornado Cash mixer contract")
            break

    if risk_score >= 60:
        return "HIGH RISK", " | ".join(reasons), "red"
    elif risk_score >= 30:
        return "MEDIUM RISK", " | ".join(reasons), "orange"
    else:
        return "LOW RISK", "No significant risk indicators identified", "green"

# --- UI ---
st.title("🛡️ Ethereum Address Risk Monitor")
st.markdown("Enter an Ethereum wallet address to analyse its on-chain transaction risk and behaviour.")

with st.sidebar:
    st.header("Settings")
    st.info("Data source: Etherscan API v2")
    st.markdown("---")
    st.markdown("**Test Addresses**")
    st.code("0x722122dF12D4e14e13Ac3b6895a86e84145b6967", language=None)
    st.caption("High Risk — Tornado Cash")
    st.code("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", language=None)
    st.caption("Low Risk — General wallet")
    st.markdown("---")
    st.caption("v1.1.0 | Etherscan API v2")

address_input = st.text_input(
    "Enter Ethereum Address (0x...)",
    placeholder="0x722122dF12D4e14e13Ac3b6895a86e84145b6967"
)

if address_input:
    if len(address_input) == 42 and address_input.startswith("0x"):
        with st.spinner("Fetching on-chain data..."):
            txs = get_tx_history(address_input)
            label, reason, color = analyze_risk(address_input, txs)

        st.subheader("Analysis Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Risk Level", label)
        col2.metric("Transactions Sampled", len(txs))
        col3.markdown(
            f"**Finding:** <span style='color:{color};font-weight:600'>{reason}</span>",
            unsafe_allow_html=True
        )

        if txs:
            st.markdown("---")
            st.subheader("Recent Transaction History")
            df = pd.DataFrame(txs)[["blockNumber", "timeStamp", "from", "to", "value", "gasUsed"]]
            df["timeStamp"] = pd.to_datetime(df["timeStamp"].astype(int), unit="s")
            df.columns = ["Block", "Timestamp", "From", "To", "Value (Wei)", "Gas Used"]
            st.dataframe(df, use_container_width=True)
    else:
        st.error("❌ Invalid Ethereum address format. Address must start with 0x and be 42 characters long.")
