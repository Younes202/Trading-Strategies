import requests
import pandas as pd
import pandas_ta as ta
import talib


def wrangle(symbol: str, interval: str, start_time: str = None, end_time: str = None, limit: int = 500):
    base_url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": interval.lower(),  # Ensure lowercase interval for consistency
        "limit": limit
    }

    if start_time:
        params["startTime"] = start_time
    if end_time:
        params["endTime"] = end_time

    # Validate interval
    valid_intervals = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
    if interval.lower() not in valid_intervals:
        raise ValueError(f"Invalid interval: {interval}. Valid intervals are: {', '.join(valid_intervals)}")

    response = requests.get(base_url, params=params)
    response.raise_for_status()  # Raise an exception for non-200 status codes

    data = response.json()

    # Create pandas DataFrame from the data
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume", "close_time",
        "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume", "ignored"
    ])

    # Convert timestamps to datetime format (optional)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")

    return df

# Test fetching data with a valid interval of "1M" (one month)
historical_data_1M = wrangle("BTCUSDT", "3m", None, None)
print("Interval Data:")
print(historical_data_1M.head())



# Apply indicators using pandas-ta
historical_data['rsi'] = ta.rsi(historical_data['close'], length=14)
historical_data['ema_50'] = ta.ema(historical_data['close'], length=50)
historical_data['sma_200'] = ta.sma(historical_data['close'], length=200)

# Apply indicators using ta-lib
historical_data['macd'], historical_data['macd_signal'], historical_data['macd_hist'] = talib.MACD(historical_data['close'])
historical_data['bb_upper'], historical_data['bb_middle'], historical_data['bb_lower'] = talib.BBANDS(historical_data['close'])



# Short term startegy
def short_term_strategy(df):
    buy_signals = []
    sell_signals = []

    for i in range(len(df)):
        if df['rsi'][i] < 30 and df['close'][i] < df['bb_lower'][i]:
            buy_signals.append(df['close'][i])
            sell_signals.append(None)
        elif df['rsi'][i] > 70 and df['close'][i] > df['bb_upper'][i]:
            buy_signals.append(None)
            sell_signals.append(df['close'][i])
        else:
            buy_signals.append(None)
            sell_signals.append(None)

    df['buy_signal'] = buy_signals
    df['sell_signal'] = sell_signals

short_term_strategy(historical_data)


# Long term strategy
def long_term_strategy(df):
    buy_signals = []
    sell_signals = []

    for i in range(len(df)):
        if df['ema_50'][i] > df['sma_200'][i]:
            buy_signals.append(df['close'][i])
            sell_signals.append(None)
        elif df['ema_50'][i] < df['sma_200'][i]:
            buy_signals.append(None)
            sell_signals.append(df['close'][i])
        else:
            buy_signals.append(None)
            sell_signals.append(None)

    df['buy_signal'] = buy_signals
    df['sell_signal'] = sell_signals

long_term_strategy(historical_data)


def backtest_strategy(df):
    initial_balance = 10000
    balance = initial_balance
    position = 0
    for i in range(len(df)):
        if df['buy_signal'][i] is not None:
            if position == 0:
                position = balance / df['buy_signal'][i]
                balance = 0
        elif df['sell_signal'][i] is not None:
            if position > 0:
                balance = position * df['sell_signal'][i]
                position = 0

    final_balance = balance + position * df['close'].iloc[-1]
    return final_balance, (final_balance - initial_balance) / initial_balance

# Short-term strategy performance
final_balance_short_term, return_short_term = backtest_strategy(historical_data)
print(f'Short-term strategy final balance: ${final_balance_short_term:.2f}, return: {return_short_term:.2%}')

# Long-term strategy performance
final_balance_long_term, return_long_term = backtest_strategy(historical_data)
print(f'Long-term strategy final balance: ${final_balance_long_term:.2f}, return: {return_long_term:.2%}')

