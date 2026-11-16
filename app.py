import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import time

# --- 1. পেজ এবং ড্যাশবোর্ড সেটআপ ---
st.set_page_config(page_title="Pro Algo Bot", page_icon="📈", layout="wide")
st.title("📈 Advanced Live Trading Dashboard")

# --- 2. সাইডবার: API এবং রিয়েল মার্কেট কনফিগারেশন ---
st.sidebar.header("⚙️ Settings & API")
api_key = st.sidebar.text_input("Delta API Key", type="password")
secret_key = st.sidebar.text_input("Delta Secret Key", type="password")

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Strategy Setup")

# স্ট্র্যাটেজি সিলেকশন (আপনার মেইন স্ট্র্যাটেজির সাথে আরও ২টো বোনাস)
strategy_choice = st.sidebar.selectbox("Select Strategy", [
    "1. 20 EMA Retest (Trend Pullback)", # আপনার দেওয়া অরিজিনাল লজিক
    "2. SuperTrend + 200 EMA",          # বোনাস স্ট্র্যাটেজি ১
    "3. RSI Divergence + VWAP"          # বোনাস স্ট্র্যাটেজি ২
])

symbol = st.sidebar.text_input("Trading Pair", value="LINK/USDT:USDT")
timeframe = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m", "1h"], index=2)

# মিনিমাম কোয়ান্টিটির জন্য ডেসিমেল ইনপুট (0.0001 স্টেপ)
trade_qty = st.sidebar.number_input("Trade Quantity", min_value=0.0001, value=1.0000, step=0.0010, format="%.4f")

# 1:2 Risk Reward (শুধুমাত্র Stop Loss দিলে Take profit অটো 2x হয়ে যাবে)
sl_percent = st.sidebar.number_input("Stop Loss (%)", min_value=0.1, value=1.0, step=0.1)
tp_percent = sl_percent * 2  # 1:2 রেশিও অনুযায়ী
st.sidebar.info(f"🎯 Target TP is Auto-set to {tp_percent:.1f}% (1:2 Risk-Reward)")

# --- 3. এক্সচেঞ্জ কানেকশন ---
@st.cache_resource
def get_exchange(api, secret):
    try:
        return ccxt.delta({
            'apiKey': api,
            'secret': secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
    except Exception as e:
        return None

exchange = get_exchange(api_key, secret_key) if api_key and secret_key else ccxt.delta({'enableRateLimit': True})

# --- 4. ডেটা ফেচ এবং ইন্ডিকেটর ক্যালকুলেশন ---
def fetch_and_calculate():
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe, limit=300)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # EMAs
        df['EMA_20'] = ta.ema(df['close'], length=20)
        df['EMA_200'] = ta.ema(df['close'], length=200)
        
        # VWAP
        df.set_index('timestamp', inplace=True)
        df['VWAP'] = ta.vwap(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'])
        df.reset_index(inplace=True)
        
        # বোনাস ইন্ডিকেটর (SuperTrend & RSI)
        supertrend = ta.supertrend(df['high'], df['low'], df['close'], length=10, multiplier=3.0)
        df['SuperTrend'] = supertrend['SUPERTd_10_3.0'] # Direction (1 = Bull, -1 = Bear)
        df['RSI'] = ta.rsi(df['close'], length=14)
        
        return df
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

# --- 5. লাইভ চার্ট ---
df = fetch_and_calculate()
if not df.empty:
    fig = go.Figure(data=[go.Candlestick(x=df['timestamp'],
                    open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Candles")])
    
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA_20'], line=dict(color='#00ff00', width=2), name="20 EMA"))
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['VWAP'], line=dict(color='#ff9900', width=2), name="VWAP"))
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA_200'], line=dict(color='#ff0000', width=3), name="200 EMA"))
    
    fig.update_layout(height=550, margin=dict(l=0, r=0, t=30, b=0), template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# --- 6. অর্ডার এক্সিকিউশন ---
def execute_trade(side, price):
    try:
        st.toast(f"Executing {side.upper()} order...", icon="⚡")
        order = exchange.create_order(symbol, 'market', side, trade_qty)
        st.success(f"✅ Entry {side.upper()} Executed! ID: {order['id']}")
        
        # 1:2 RR Price Calculation
        if side == 'buy':
            tp_price = price * (1 + (tp_percent / 100))
            sl_price = price * (1 - (sl_percent / 100))
            close_side = 'sell'
        else:
            tp_price = price * (1 - (tp_percent / 100))
            sl_price = price * (1 + (sl_percent / 100))
            close_side = 'buy'
            
        tp_params = {'triggerPrice': round(tp_price, 4), 'reduceOnly': True}
        sl_params = {'triggerPrice': round(sl_price, 4), 'reduceOnly': True}
        
        exchange.create_order(symbol, 'take_profit_market', close_side, trade_qty, params=tp_params)
        st.success(f"🎯 Take Profit (1:2) Placed at {round(tp_price, 4)}")
        
        exchange.create_order(symbol, 'stop_market', close_side, trade_qty, params=sl_params)
        st.error(f"🛑 Stop Loss Placed at {round(sl_price, 4)}")
        
    except Exception as e:
        st.error(f"Execution Failed: {e}")

# --- 7. বট কন্ট্রোল ---
st.markdown("---")
col1, col2 = st.columns(2)
if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False

with col1:
    if st.button("▶️ START BOT", use_container_width=True):
        if not api_key:
            st.warning("API Key দিন!")
        else:
            st.session_state.bot_running = True
            st.success("Bot Started! Looking for setups...")

with col2:
    if st.button("⏹️ STOP BOT", use_container_width=True):
        st.session_state.bot_running = False
        st.error("Bot Stopped.")

# --- 8. অটোমেটেড ট্রেডিং লজিক ---
if st.session_state.bot_running and not df.empty:
    last_close = df['close'].iloc[-1]
    last_low = df['low'].iloc[-1]
    last_high = df['high'].iloc[-1]
    
    last_ema_20 = df['EMA_20'].iloc[-1]
    last_ema_200 = df['EMA_200'].iloc[-1]
    last_vwap = df['VWAP'].iloc[-1]
    
    st.write(f"**Current Check:** P: {last_close} | 20 EMA: {last_ema_20:.4f} | VWAP: {last_vwap:.4f} | 200 EMA: {last_ema_200:.4f}")
    
    # === STRATEGY 1: 20 EMA Retest (আপনার দেওয়া অরিজিনাল লজিক) ===
    if "1. 20 EMA Retest" in strategy_choice:
        # BUY Condition
        buy_trend = (last_close > last_ema_200) and (last_vwap > last_ema_200) and (last_ema_20 > last_vwap)
        buy_retest = (last_low <= last_ema_20 * 1.002) and (last_close > last_ema_20) # প্রাইস 20 EMA টাচ করে উপরে ক্লোজ দিলে
        
        # SELL Condition
        sell_trend = (last_close < last_ema_200) and (last_vwap < last_ema_200) and (last_ema_20 < last_vwap)
        sell_retest = (last_high >= last_ema_20 * 0.998) and (last_close < last_ema_20) # প্রাইস 20 EMA টাচ করে নিচে ক্লোজ দিলে
        
        if buy_trend and buy_retest:
            execute_trade('buy', last_close)
            st.session_state.bot_running = False
            st.rerun()
            
        elif sell_trend and sell_retest:
            execute_trade('sell', last_close)
            st.session_state.bot_running = False
            st.rerun()

    # === STRATEGY 2: SuperTrend + 200 EMA (বোনাস) ===
    elif "2. SuperTrend" in strategy_choice:
        last_st_dir = df['SuperTrend'].iloc[-1]
        
        if last_st_dir == 1 and last_close > last_ema_200:
            execute_trade('buy', last_close)
            st.session_state.bot_running = False
            st.rerun()
        elif last_st_dir == -1 and last_close < last_ema_200:
            execute_trade('sell', last_close)
            st.session_state.bot_running = False
            st.rerun()

    # === STRATEGY 3: RSI Divergence (Overbought/Oversold) + VWAP (বোনাস) ===
    elif "3. RSI" in strategy_choice:
        last_rsi = df['RSI'].iloc[-1]
        
        if last_rsi < 30 and last_close > last_vwap: # Oversold থেকে রিকভারি
            execute_trade('buy', last_close)
            st.session_state.bot_running = False
            st.rerun()
        elif last_rsi > 70 and last_close < last_vwap: # Overbought থেকে ড্রপ
            execute_trade('sell', last_close)
            st.session_state.bot_running = False
            st.rerun()

    time.sleep(10)
    st.rerun()
