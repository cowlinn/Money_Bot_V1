import numpy as np
import pandas as pd
import talib
# import yfinance as yf

"""""
symbol = "AAPL"
data_period = '21d'
interval = "1h"

# Retrieve intraday price data using Yahoo Finance API
df = yf.Ticker(symbol).history(period = data_period, interval=interval)

df["AD"] = talib.AD(df["High"], df["Low"], df["Close"], df["Volume"])
df["ADOSC"] = talib.ADOSC(df["High"], df["Low"], df["Close"], df["Volume"], fastperiod=3, slowperiod=10)
df["ADX"] = talib.ADX(df["High"], df["Low"], df["Close"], timeperiod=14)
df["ADXR"] = talib.ADXR(df["High"], df["Low"], df["Close"], timeperiod=14)
df["DX"] = talib.DX(df["High"], df["Low"], df["Close"], timeperiod=14)
df["BBANDS_upper"], df["BBANDS_middle"], df["BBANDS_lower"] = talib.BBANDS(df["Close"], timeperiod=20, nbdevup=2, nbdevdn=2)
df["BETA"] = talib.BETA(df["High"], df["Low"], timeperiod=5)

df["MACD"], df["MACD_signal"], df["MACD_hist"] = talib.MACD(df["Close"], fastperiod=12, slowperiod=26, signalperiod=9)
df["MFI"] = talib.MFI(df["High"], df["Low"], df["Close"], df["Volume"], timeperiod=14)
df["ROC"] = talib.ROC(df["Close"], timeperiod=12)
df["ROCP"] = talib.ROCP(df["Close"], timeperiod=12)
df["ROCR"] = talib.ROCR(df["Close"], timeperiod=12)
df["ROCR100"] = talib.ROCR100(df["Close"], timeperiod=12)
df["RSI"] = talib.RSI(df["Close"], timeperiod=14)
df["SAR"] = talib.SAR(df["High"], df["Low"], acceleration=0.02, maximum=0.2)
df["STOCH_slowk"], df["STOCH_slowd"] = talib.STOCH(df["High"], df["Low"], df["Close"], fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
df["TRIX"] = talib.TRIX(df["Close"], timeperiod=30)
df["WCLPRICE"] = talib.WCLPRICE(df["High"], df["Low"], df["Close"])
"""


#############################################################################################################################################################################################




def wma_strategy(data):
    data['wma'] = talib.WMA(data['Close'], timeperiod=10)  
    data['wma_shifted'] = data['wma'].shift(1)  

    data['buy_signal'] = np.where(data['Close'] > data['wma_shifted'], 1, 0)
    data['sell_signal'] = np.where(data['Close'] < data['wma_shifted'], -1, 0)

    return data


def ema_strategy(data):
    data['ema'] = talib.EMA(data['Close'], timeperiod=10)  
    data['ema_shifted'] = data['ema'].shift(1)  

    data['buy_signal'] = np.where(data['Close'] > data['ema_shifted'], 1, 0)
    data['sell_signal'] = np.where(data['Close'] < data['ema_shifted'], -1, 0)

    return data


def kama_strategy(data):
    data['kama'] = talib.KAMA(data['Close'], timeperiod=10) 
    data['kama_shifted'] = data['kama'].shift(1)  

    data['buy_signal'] = np.where(data['Close'] > data['kama_shifted'], 1, 0)
    data['sell_signal'] = np.where(data['Close'] < data['kama_shifted'], -1, 0)

    return data


def comprehensive_strategy(data):
    data = wma_strategy(data)  
    data = ema_strategy(data)  
    data = kama_strategy(data)  

    data['buy_signal_combined'] = data[['buy_signal_wma', 'buy_signal_ema', 'buy_signal_kama']].sum(axis=1)
    data['sell_signal_combined'] = data[['sell_signal_wma', 'sell_signal_ema', 'sell_signal_kama']].sum(axis=1)

    return data


def ad_strategy(data):
    data['ad'] = talib.AD(data['High'], data['Low'], data['Close'], data['Volume']) 
    data['adosc'] = talib.ADOSC(data['High'], data['Low'], data['Close'], data['Volume'], fastperiod=3, slowperiod=10)  
    data['buy_signal'] = np.where(data['adosc'] > 0, 1, 0)
    data['sell_signal'] = np.where(data['adosc'] < 0, -1, 0)

    return data


def adx_strategy(data):
    data['adx'] = talib.ADX(data['High'], data['Low'], data['Close'], timeperiod=14)  
    data['adxr'] = talib.ADXR(data['High'], data['Low'], data['Close'], timeperiod=14)  
    data['dx'] = talib.DX(data['High'], data['Low'], data['Close'], timeperiod=14)  

    data['buy_signal'] = np.where((data['adx'] > 25) & (data['adx'] > data['adx'].shift(1)) & (data['dx'] > data['adxr']), 1, 0)
    data['sell_signal'] = np.where((data['adx'] > 25) & (data['adx'] > data['adx'].shift(1)) & (data['dx'] < data['adxr']), -1, 0)

    return data


def bbands_strategy(data):
    upper, middle, lower = talib.BBANDS(data['Close'], timeperiod=20)  

    data['buy_signal'] = np.where(data['Close'] < lower, 1, 0)
    data['sell_signal'] = np.where(data['Close'] > upper, -1, 0)

    return data


def beta_strategy(data):
    market_returns = market_data['Close'].pct_change()  # Calculate market returns
    stock_returns = data['Close'].pct_change()  # Calculate stock returns

    data['beta'] = stock_returns.rolling(window=30).cov(market_returns) / market_returns.rolling(window=30).var() 

    data['buy_signal'] = np.where(data['beta'] > 1, 1, 0)
    data['sell_signal'] = np.where(data['beta'] < 1, -1, 0)

    return data

def macd_strategy(data):
    macd = talib.MACD(data['Close'])[2]
    latest_val = macd.iloc[-1]
    previous_val = macd.iloc[-2]
    if latest_val > 0 and previous_val < 0:
        return 1
    if latest_val < 0 and previous_val > 0:
        return -1
    else:
        return 0

def mfi_strategy(data):
    MFI = talib.MFI(data['High'], data['Low'], data['Close'], data['Volume'], timeperiod=14)  
    latest_val = MFI.iloc[-1]
    if latest_val > 80:
        return -1
    elif latest_val < 20:
        return 1
    else:
        return 0


def roc_strategy(data):
    data['roc'] = talib.ROC(data['Close'], timeperiod=12)
    data['rocp'] = talib.ROCP(data['Close'], timeperiod=12)  
    data['rocr'] = talib.ROCR(data['Close'], timeperiod=12)  
    data['rocr100'] = talib.ROCR100(data['Close'], timeperiod=12) 

    data['buy_signal_roc'] = np.where(data['roc'] > 0, 1, 0)
    data['sell_signal_roc'] = np.where(data['roc'] < 0, -1, 0)

    data['buy_signal_rocp'] = np.where(data['rocp'] > 0, 1, 0)
    data['sell_signal_rocp'] = np.where(data['rocp'] < 0, -1, 0)

    data['buy_signal_rocr'] = np.where(data['rocr'] > 1, 1, 0)
    data['sell_signal_rocr'] = np.where(data['rocr'] < 1, -1, 0)

    data['buy_signal_rocr100'] = np.where(data['rocr100'] > 1, 1, 0)
    data['sell_signal_rocr100'] = np.where(data['rocr100'] < 1, -1, 0)

    return data


def rsi_strategy(data):
    RSI = talib.RSI(data['Close'], timeperiod=14)
    latest_val = RSI.iloc[-1]
    if latest_val < 30:
        return 1
    elif latest_val >70:
        return -1
    else:
        return 0

def rsi_sma_strategy(data):
    RSI = talib.RSI(data['Close'], timeperiod=14)
    rolling_window = 14
    RSI_sma = pd.Series(RSI).rolling(rolling_window).mean() # SMA of RSI over 14 periods
    latest_val = RSI_sma.iloc[-1]
    if latest_val < 30:
        return 1
    elif latest_val >70:
        return -1
    else:
        return 0


def sar_strategy(data):
    data['sar'] = talib.SAR(data['High'], data['Low'], acceleration=0.02, maximum=0.2) 

    data['buy_signal'] = np.where(data['Close'] > data['sar'], 1, 0)
    data['sell_signal'] = np.where(data['Close'] < data['sar'], -1, 0)

    return data


def stochrsi_strategy(data):
    data['fastk'], data['fastd'] = talib.STOCHRSI(data['Close'], timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0)  

    data['buy_signal'] = np.where((data['fastk'] < 20) & (data['fastd'] < 20), 1, 0)
    data['sell_signal'] = np.where((data['fastk'] > 80) & (data['fastd'] > 80), -1, 0)

    return data


def trix_strategy(data):
    TRIX = talib.TRIX(data['Close'], timeperiod=18) 
    latest_val = TRIX.iloc[-1]
    previous_val = TRIX.iloc[-2]
    if latest_val > 0 and previous_val < 0:
        return 1
    if latest_val < 0 and previous_val > 0:
        return -1
    else:
        return 0

def TA(data):
    df = pd.DataFrame()
    # indicators we using
    df['RSI'] = [rsi_strategy(data)]
    df['RSI_SMA'] = rsi_sma_strategy(data)
    df['MACD'] = macd_strategy(data)
    df['MFI'] = mfi_strategy(data)
    df['TRIX'] = trix_strategy(data)
    return df