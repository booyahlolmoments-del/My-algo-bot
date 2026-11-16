import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# App Configuration
st.set_page_config(page_title="Personal Algo Trader", page_icon="📈", layout="wide")

# Sidebar Menu
st.sidebar.title("🤖 Algo Bot Menu")
page = st.sidebar.radio("Navigation", ["Live Dashboard", "Strategy Setup", "Performance Analytics", "Settings"])

# ==========================================
# PAGE 1: LIVE DASHBOARD
# ==========================================
if page == "Live Dashboard":
    st.title("📈 Live Trading Dashboard")
    st.write("Monitor your active bot and live market status here.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Live Market (Placeholder)")
        # In the future, real CCXT chart data will be displayed here
        chart_data = pd.DataFrame(np.random.randn(50, 1) * 2 + 10, columns=["Price"])
        st.line_chart(chart_data)
        
    with col2:
        st.subheader("Bot Control")
        if st.button("▶️ START BOT", use_container_width=True, type="primary"):
            st.success("Bot Started! Scanning for setups...")
            
        if st.button("⏹️ STOP BOT", use_container_width=True):
            st.warning("Bot Stopped.")
            
        st.divider()
        st.write("**Active Coin:** LINK/USDT")
        st.write("**Active Strategy:** 200 EMA + VWAP Pullback 1:2")
        st.write("**Status:** 🟢 Running")

# ==========================================
# PAGE 2: STRATEGY SETUP
# ==========================================
elif page == "Strategy Setup":
    st.title("⚙️ Strategy Setup")
    st.write("Configure your trading rules and strategies before starting the bot.")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_coin = st.selectbox("Select Coin", ["LINK/USDT", "BTC/USDT", "ETH/USDT", "SOL/USDT"])
        selected_timeframe = st.selectbox("Timeframe", ["5m", "15m", "1H", "4H"])
        
    with col2:
        strategies = [
            "Diamond Asset Strategy 2.0 (Custom)",
            "200 EMA + VWAP Pullback 1:2 (Custom)",
            "MACD + RSI Divergence",
            "Bollinger Bands Mean Reversion",
            "ICT Silver Bullet / FVG Strategy"
        ]
        selected_strategy = st.selectbox("Select Strategy", strategies)
        risk_per_trade = st.number_input("Risk Per Trade (USD)", min_value=0.5, value=25.0, step=0.5)
        
    st.info(f"Summary: You are setting up to trade **{selected_coin}** on a **{selected_timeframe}** timeframe using **{selected_strategy}** with a risk of **${risk_per_trade}** per trade.")
    
    if st.button("Save Configuration"):
        st.success("Strategy parameters saved successfully!")

# ==========================================
# PAGE 3: PERFORMANCE ANALYTICS
# ==========================================
elif page == "Performance Analytics":
    st.title("📊 Performance Analytics")
    st.write("Track your trade history, win rate, and execution logic.")
    
    # Dummy Trade History (To be replaced with database/CSV data later)
    data = {
        "Date": [datetime.now().strftime("%Y-%m-%d %H:%M")] * 4,
        "Coin": ["LINK/USDT", "LINK/USDT", "LINK/USDT", "LINK/USDT"],
        "Logic": ["VWAP Rejection (Short)", "Diamond Color Change", "200 EMA Bounce (Long)", "VWAP Rejection (Long)"],
        "Entry": [9.963, 9.900, 9.820, 9.852],
        "SL": [10.050, 9.850, 9.750, 9.750],
        "TP": [9.789, 10.000, 9.960, 10.056],
        "Result": ["Win", "Loss", "Win", "Running"],
        "PnL ($)": ["+50.00", "-25.00", "+50.00", "0.00"]
    }
    df = pd.DataFrame(data)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Trades", "3")
    m2.metric("Win Rate", "66.6%")
    m3.metric("Total PnL", "+$75.00")
    m4.metric("Active Trades", "1")
    
    st.divider()
    st.subheader("Trade History Log")
    
    def color_result(val):
        color = '#00FF00' if val == 'Win' else '#FF0000' if val == 'Loss' else '#FFA500'
        return f'color: {color}; font-weight: bold'
        
    st.dataframe(df.style.map(color_result, subset=['Result']), use_container_width=True)

# ==========================================
# PAGE 4: SETTINGS
# ==========================================
elif page == "Settings":
    st.title("🔒 API Settings")
    st.write("Enter your Delta Exchange API credentials securely.")
    
    api_key = st.text_input("Delta Exchange API Key", type="password")
    api_secret = st.text_input("Delta Exchange API Secret", type="password")
    
    if st.button("Save API Keys"):
        if api_key and api_secret:
            st.success("API Keys securely saved!")
        else:
            st.error("Please enter both your API Key and Secret.")
