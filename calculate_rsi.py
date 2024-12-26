import numpy as np
import pandas as pd
import requests

keys = [
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_asset_volume",
    "number_of_trades",
    "taker_buy_base_asset_volume",
    "taker_buy_quote_asset_volume",
    "ignore"
]

def calculate_rsi(price_data):
    # Chuyển đổi dữ liệu sang DataFrame
    prices = pd.DataFrame(price_data)
    prices['close'] = prices['close'].astype(float)
    
    # Tính toán lợi nhuận
    prices['diff'] = prices['close'].diff()
    prices['gain'] = np.where(prices['diff'] > 0, prices['diff'], 0)
    prices['loss'] = np.where(prices['diff'] < 0, -prices['diff'], 0)
    
    # Chu kỳ RSI (thường là 14, nhưng có thể điều chỉnh)
    window_length = 5
    
    # Tính trung bình động
    avg_gain = prices['gain'].rolling(window=window_length, min_periods=1).mean()
    avg_loss = prices['loss'].rolling(window=window_length, min_periods=1).mean()
    
    # Tính RS và RSI
    rs = avg_gain / avg_loss
    prices['RSI'] = 100 - (100 / (1 + rs))
    
    # Thêm RSI vào json cũ
    for i, rsi in enumerate(prices['RSI']):
        price_data[i]['RSI'] = rsi
    
    return price_data


def get_historical_data(symbol, interval, limit=100):
    result = []
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
        result.append(json_result)
        
    return result

    
result = get_historical_data("BTCUSDT", "1h", 1000)
updated_result = calculate_rsi(result)
print(updated_result)
