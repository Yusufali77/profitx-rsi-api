from flask import Flask, jsonify
import ccxt
import pandas as pd

app = Flask(__name__)

# Bybit API bağlantısı
bybit = ccxt.bybit({
    'apiKey': '8eUQ1PQoFGhDO6czVk',
    'secret': '4zmpgjLHZxamK14OwuFRgYIaPykre8kQNdPf',
    'enableRateLimit': True
})

# RSI endpoint
@app.route('/api/rsi')
def rsi():
    ohlcv = bybit.fetch_ohlcv('BTC/USDT', '1h', limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return jsonify({'symbol': 'BTC/USDT', 'rsi': round(rsi.iloc[-1], 2)})

# MACD endpoint
@app.route('/api/macd')
def macd():
    ohlcv = bybit.fetch_ohlcv('BTC/USDT', '1h', limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    return jsonify({
        'macd': round(macd_line.iloc[-1], 2),
        'signal': round(signal_line.iloc[-1], 2)
    })

# Candlestick colors endpoint
@app.route('/api/candles')
def candles():
    ohlcv = bybit.fetch_ohlcv('BTC/USDT', '1h', limit=3)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    candles = []
    for _, row in df.iterrows():
        color = "green" if row['close'] > row['open'] else "red"
        candles.append({
            'open': row['open'],
            'close': row['close'],
            'color': color
        })
    return jsonify({'candles': candles})

# Insight endpoint (hepsi bir arada)
@app.route('/api/insight')
def insight():
    ohlcv = bybit.fetch_ohlcv('BTC/USDT', '1h', limit=100)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    rsi_val = 100 - (100 / (1 + rs)).iloc[-1]

    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    macd_val = (exp1 - exp2).iloc[-1]
    signal_val = (exp1 - exp2).ewm(span=9, adjust=False).mean().iloc[-1]

    # Candles
    candles_df = bybit.fetch_ohlcv('BTC/USDT', '1h', limit=3)
    candle_df = pd.DataFrame(candles_df, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    last_candles = ["green" if row['close'] > row['open'] else "red" for _, row in candle_df.iterrows()]

    # GPT-stil yorum
    if rsi_val < 30 and macd_val > signal_val and last_candles[-1] == "green":
        comment = "🟢 Güçlü alım sinyali: RSI düşük, MACD yukarı kesmiş, son mum yeşil."
    elif rsi_val > 70 and macd_val < signal_val and last_candles[-1] == "red":
        comment = "🔴 Aşırı alım bölgesi: RSI yüksek, MACD aşağı kesmiş, son mum kırmızı."
    else:
        comment = "⚪ Piyasa kararsız: Net bir sinyal oluşmamış."

    return jsonify({
        'rsi': round(rsi_val, 2),
        'macd': round(macd_val, 2),
        'signal': round(signal_val, 2),
        'candles': last_candles,
        'comment': comment
    })

# Uygulama başlat
if __name__ == '__main__':
    app.run(debug=True)
