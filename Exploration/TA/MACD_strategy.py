import talib as ta
import yfinance as yf
import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
import datetime
import time
stock_name = "SPY"
data_period = "2d"
resolution = "5m"
time_interval = 1 # time interval from today in days (when do we want to hit the target price?)
shift = int(time_interval) # converts time interval into however many 15 min blocks. Note that there are 6.5 trading hours in a trading day
# formula for 1d resolution and for all integer time interval is int(time_interval)
# formula for 1h resolution and integer day time interval is int(time_interval*7)
# formula for 15m resolution and 1 day time interval is int(time_interval*6.5*4)
# formula for 15m resolution and 15m time interval (=1) is int(time_interval)
# formula for 1m resolution and 1 day time interval is int(time_interval*6.5*60)     
# formula for 1m resolution and 15 min time interval (1/(6.5*4)) is int(time_interval*6.5*60)
stock = yf.Ticker(stock_name)  # this goes in main()
hist = stock.history(period = data_period, interval = resolution) # historical price data
price = hist['Close']

def MACDstrat(price):
    macd = ta.MACD(price)
    # macd[0] is the 12 period EMA
    # macd[1] is the 26 period EMA
    # macd[2] is just macd[0] - macd[1] (this is what we actually want to use)
    # if macd[2] goes from > 0 to < 0, that is considered a cross downwards, signalling a likely fall in share price
    # if macd[2] goes from < 0 to > 0, that is considered a cross upwards, signalling a likely rise in share price
    latest_macd = macd[2][-1]
    previous_macd = macd[2][-2]
    # print(latest_macd)
    # print(previous_macd)
    cross = 0
    # bruh this is just setting cross to 0 every time we call the function??
    # pls fix this so that it actually remembers what the previous cross was
    # or add some way to recognize if this is the first time the function is called, then set cross to be 1 or -1
    
    # first trade of the day
    if cross == 0:
        # cross downwards
        if previous_macd > 0 and latest_macd < 0:
            cross = -1
            print('Buy a put!') # execute some buy order
            return('Buy a put!', macd[2][-1])
        
        # cross upwards
        elif previous_macd < 0 and latest_macd > 0:
            cross = 1
            print('Buy a call!') # execute some buy order
            return('Buy a call!', macd[2][-1])
    
    # if the last trade we entered was buying a put
    elif cross == -1:
        if previous_macd < 0 and latest_macd > 0:
            cross = 1
            print('Sell the put and buy a call!') # execute some buy order
    
    # if the last trade we entered was buying a call
    elif cross == 1:
        # cross downwards
        if previous_macd > 0 and latest_macd < 0:
            cross = -1
            print('Sell the put and buy a put!') # execute some buy order
    
    # need some other if statement to detect if the trade is past a certain point in the day
    # or just close all positions if time > 3pm US time?
    # or maybe don't enter any trades past 2pm US time?
    return ('No crossover.', macd[2][-1]) # for now it just returns the latest macd value

# visualisation purposes, uncomment to view MACD graphs

macd = ta.MACD(price)
x_vals = range(len(macd[0]))
plt.subplot(2,1,1)
plt.title('MACD graph for '+ stock_name)
plt.plot(x_vals, macd[0]) # blue line
plt.plot(x_vals, macd[1]) # orange line
plt.grid()


plt.subplot(2,1,2)
plt.plot(x_vals, macd[2])
plt.grid()

def caveman_loop():
    buffer = 0
    while True:
        now = datetime.datetime.now()
        if now.minute%5 == 0:
            time.sleep(3) # 1 second for yahoo finance to update lmao (may be unnecessary?)
            # call the data
            stock = yf.Ticker("SPY")
            price = stock.history(period = '2d', interval = '5m')['Close']
            macd = MACDstrat(price)
            print(now)
            print('Price is ' + str(round(price[-1], 3)) + '.', macd[0])
            time.sleep(60)
            if buffer == macd[1]:
                break
            buffer = macd[1]
                
            
            
        
