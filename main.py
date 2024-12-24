import json
import websocket
import pandas as pd

# Tên biến sửa lại cho chính xác
assets = ["BTCUSDT"]
assets = [coin.lower() + "@kline_1m" for coin in assets]
assets = "/".join(assets)
print(assets)

def on_message(ws, message):
    message = json.loads(message)
    manipulation(message)

def manipulation(source):
    rel_data = source["data"]["k"]["c"]  # Giá đóng cửa
    evt_time = pd.to_datetime(source["data"]["E"], unit="ms")
    
    # Chuyển thành DataFrame
    df = pd.DataFrame([[rel_data]], columns=[source["data"]["s"]], index=[evt_time])
    df.index.name = "timestamp"
    df = df.astype(float)
    df.reset_index()
    print(df)

socket = f"wss://stream.binance.com:9443/stream?streams={assets}"

# Kết nối WebSocket
ws = websocket.WebSocketApp(socket, on_message=on_message)
ws.run_forever()
