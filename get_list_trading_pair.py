import requests

def get_binance_symbol_pairs():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        symbols = data['symbols']
        pairs = [symbol['symbol'] for symbol in symbols if symbol['status'] == 'TRADING']
        return pairs
    else:
        print(f"Error: {response.status_code}")
        return []

pairs = get_binance_symbol_pairs()
print(f"Tổng số: {len(pairs)}")
print(len([i for i in pairs if str(i).endswith("USDT")]))
print(len([i for i in pairs if str(i).endswith("BTC")]))

