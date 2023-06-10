import yfinance as yf
import numpy as np

# for testing, remove when done
stock_name = "SPY"
data_period = "30d"
resolution = "5m"
stock = yf.Ticker(stock_name)  # this goes in main()
df = stock.history(period = data_period, interval = resolution) # historical price data
def gain(x):
    return ((x > 0) * x).sum()


def loss(x):
    return ((x < 0) * x).sum()
def mfi(high, low, close, volume, n=14):
    typical_price = (high + low + close)/3
    money_flow = typical_price * volume
    mf_sign = np.where(typical_price > typical_price.shift(1), 1, -1)
    signed_mf = money_flow * mf_sign
    mf_avg_gain = signed_mf.rolling(n).apply(gain, raw=True)
    mf_avg_loss = signed_mf.rolling(n).apply(loss, raw=True)
    return (100 - (100 / (1 + (mf_avg_gain / abs(mf_avg_loss))))).to_numpy()
# for i in range(100):
#     test = mfi(df['High'], df['Low'], df['Close'], df['Volume'], i)
#     print(i, test[-1], test[-2])