from datetime import datetime, timezone
import pandas as pd
import requests

keys = ["timestamp", "open", "high", "low", "close", "volume", "close_time", 
        "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume", 
        "taker_buy_quote_asset_volume", "ignore"]

def get_historical_data(symbol, interval, limit=100):
    url = f"https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    for dt in data:
        json_result = dict(zip(keys, dt))
        print(json_result)

    # Chuyển đổi dữ liệu thành DataFrame
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["close"] = df["close"].astype(float)
    df.set_index("timestamp", inplace=True)
    
    return df


def calculate_rsi(df, period=14):
    delta = df['close'].diff()  # Tính sự thay đổi giá
    gain = delta.where(delta > 0, 0)  # Lọc ra phần tăng
    loss = -delta.where(delta < 0, 0)  # Lọc ra phần giảm
    
    # Tính giá trị trung bình của gain và loss trong mỗi chu kỳ
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    # Tránh chia cho 0
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    print(rsi)
    
    df['RSI'] = rsi
    return df

data = get_historical_data("BTCUSDT", "1h")
print(calculate_rsi(data))