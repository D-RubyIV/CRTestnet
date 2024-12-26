import sys
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPainter, QImage
from threading import Thread

import websocket

# Lấy dữ liệu lịch sử từ Binance
def get_historical_data(symbol, interval, limit=10000):
    url = f"https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Chuyển đổi dữ liệu thành DataFrame
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["close"] = df["close"].astype(float)
    df.set_index("timestamp", inplace=True)
    
    return df

# Tính RSI từ giá đóng cửa
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
    
    df['RSI'] = rsi
    return df

# Khởi tạo cửa sổ PySide6
class ChartWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("BTC/USDT Chart")
        self.setGeometry(100, 100, 800, 600)
        
        self.layout = QVBoxLayout()
        self.label = QLabel("Realtime BTC/USDT Data", self)
        self.layout.addWidget(self.label)

        self.setLayout(self.layout)

        # Dữ liệu ban đầu cho biểu đồ (lấy dữ liệu lịch sử)
        self.data = get_historical_data("BTCUSDT", "1m", limit=100)
        self.data = calculate_rsi(self.data)  # Tính RSI cho dữ liệu
        print(self.data)
        self.fig, (self.ax_price, self.ax_rsi) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

    def update_chart(self):
        # Vẽ lại biểu đồ với dữ liệu mới
        self.ax_price.clear()
        self.ax_rsi.clear()

        # Biểu đồ giá đóng cửa
        self.ax_price.plot(self.data.index, self.data["close"], label="BTC/USDT Close Price")
        self.ax_price.set_title("Realtime BTC/USDT Price")
        self.ax_price.set_ylabel("Price (USDT)")
        self.ax_price.legend()

        # Biểu đồ RSI
        self.ax_rsi.plot(self.data.index, self.data["RSI"], label="RSI", color='orange')
        self.ax_rsi.set_title("RSI")
        self.ax_rsi.set_xlabel("Time")
        self.ax_rsi.set_ylabel("RSI")
        self.ax_rsi.axhline(70, color='red', linestyle='--')  # Dòng mức overbought
        self.ax_rsi.axhline(30, color='green', linestyle='--')  # Dòng mức oversold
        self.ax_rsi.legend()

        self.fig.canvas.draw()

    def plot_to_qimage(self):
        # Chuyển biểu đồ Matplotlib thành QImage để hiển thị trong PySide6
        self.fig.canvas.draw()
        img = self.fig.canvas.buffer_rgba()
        img = QImage(img, self.fig.canvas.width(), self.fig.canvas.height(), QImage.Format_RGBA8888)
        return img

    def paintEvent(self, event):
        img = self.plot_to_qimage()
        painter = QPainter(self)
        painter.drawImage(0, 0, img)
        painter.end()

# Khởi tạo ứng dụng WebSocket
class BinanceWebSocket:
    def __init__(self, chart_window):
        self.chart_window = chart_window

    def on_message(self, ws, message):
        message = json.loads(message)
        print(message)
        self.manipulation(message)

    def manipulation(self, source):
        try:
            rel_data = float(source["data"]["k"]["c"])  # Giá đóng cửa
            evt_time = pd.to_datetime(source["data"]["E"], unit="ms")

            # Thêm dữ liệu mới vào DataFrame
            new_data = pd.DataFrame([[evt_time, rel_data]], columns=["timestamp", "close"])
            self.chart_window.data = pd.concat([self.chart_window.data, new_data], ignore_index=True)

            # Tính lại RSI sau khi thêm dữ liệu mới
            self.chart_window.data = calculate_rsi(self.chart_window.data)

            # Cập nhật biểu đồ
            self.chart_window.update_chart()
            self.chart_window.repaint()  # Đảm bảo vẽ lại biểu đồ trong cửa sổ PySide6
        except KeyError as e:
            print(f"Lỗi với dữ liệu: {e}")
        except ValueError as e:
            print(f"Lỗi chuyển đổi giá trị: {e}")

    def run(self, socket_url):
        ws = websocket.WebSocketApp(socket_url, on_message=self.on_message)
        ws.run_forever()

# Khởi tạo ứng dụng PySide6
def main():
    app = QApplication(sys.argv)

    # Tạo cửa sổ biểu đồ
    chart_window = ChartWindow()
    chart_window.show()

    # Kết nối WebSocket để nhận dữ liệu từ Binance
    socket_url = "wss://stream.binance.com:9443/stream?streams=btcusdt@kline_1m"
    binance_ws = BinanceWebSocket(chart_window)
    
    # Chạy WebSocket trong một luồng riêng biệt
    ws_thread = Thread(target=binance_ws.run, args=(socket_url,))
    ws_thread.start()

    # Chạy ứng dụng PySide6
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
