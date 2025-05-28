from flask import Flask, jsonify
import ccxt
import pandas as pd

app = Flask(__name__)

bybit = ccxt.bybit({
    'apiKey': '8eUQ1PQoFGhDO6czVk',
    'secret': '4zmpgjLHZxamK14OwuFRgYIaPykre8kQNdPf',
    'enableRateLimit': True
})

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

if __name__ == '__main__':
    app.run(debug=True)
