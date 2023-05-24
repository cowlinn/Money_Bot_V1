# All Imports
from matplotlib import pyplot as plt
import yfinance as yf
import talib as ta
import pandas as pd


fb = yf.Ticker("META")
df = fb.history(start="2022-01-03")

plt.style.use('fivethirtyeight')
df['MA'] = ta.SMA(df['Close'],timeperiod=5)
df[['Close','MA']].plot(figsize=(8,8))


df['MA'] = ta.SMA(df['Close'],timeperiod=5)
df['EMA'] = ta.EMA(df['Close'], timeperiod = 5)
df[['Close','MA','EMA']].plot(figsize=(8,8))


df['RSI'] = ta.RSI(df['Close'],14)
df['RSI'].plot(figsize=(8,8),marker='o')
df.tail(10)

plt.show()