import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math
import random

def derivative(x):
    return x - x.shift()

def f(x):
    x = x.dropna()
    absx = abs(x)
    absx_lst = absx.tolist()
    x_lst = x.tolist()
    y = []
    for i in range(len(x_lst)):
        if absx_lst[i] > absx.mean() and x_lst[i]>0:
            i = 1
        elif absx_lst[i] > absx.mean() and x_lst[i]<0:
            i = -1
        else:
            i = 0
        y.append(i)

    for i in range(1, (len(y)-1)):
        magnitude = 1
        while absx_lst[i] > (absx.mean() + magnitude*x.std()) and y[i]>0:
            y[i] += 1
            magnitude +=1
    for i in range(1, (len(y)-1)):
        magnitude = 1
        while absx_lst[i] > (absx.mean() + magnitude*x.std()) and y[i]<0:
            y[i] -= 1
            magnitude +=1

    for i in range(1, (len(y)-1)):
        if y[i] == 0 and y[i+1] == y[i-1]:
            y[i] = y[i-1]
    for i in range(1, (len(y)-1)):
        if y[i] != 0 and y[i+1] == 0 and y[i-1] == 0:
            y[i] = 0
    rolling_window = 4
    y_smooth = pd.Series(y).rolling(rolling_window).mean()
    # for i in range(rolling_window-1):
    #     y[i] = np.nan
    y_chunky = pd.Series(y)
    # now take rolling average?
    # this kind of helps to smooth out the cluster graph but it doesn't really help to identify cluster boundaries?
    # y is the cluster data
    return y_smooth, y_chunky, rolling_window

def shape_visual(x, name, price): # plot the time dependence of a variable in one plot and the identified clusters in another plot
    y = f(x)[1]   # [0] is smoothed data, [1] is chunky data
    # tbh smooth shows price movements more accurately (can eliminate like 'irrelevant' volatility)
    # since we are interested in catching large directional moves
    plt.subplot(3,1,1)
    plt.plot(range(len(x)), (x))
    name = name + ' time dependence'
    plt.title(name)
    plt.grid()
    plt.subplot(3,1,2)
    plt.plot(range(len(y)), y)
    # f() is some function that tries to identify where clusters are located
    clust_name = "cluster detection"
    plt.title(clust_name)
    plt.tight_layout(pad=1.0)
    plt.grid()
    
    plt.subplot(3,1,3)
    name = 'price'
    plt.title(name)
    plt.grid()
    plt.plot(range(len(price)), price)
    plt.show()

stock_name = "msft"
data_period = "1y"
resolution = "1d"
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
hist.reset_index(inplace=True) # converts datetime to a column
hist['time_index'] = range(-len(hist.index), 0)
hist['time_index'] += 1
price = hist['Close']
increase = price - price.shift(shift)
percentage_increase = (increase/price.shift()*100).dropna()
latest_price = hist['Close'][len(hist['Close'])-1]
hist['increase'] = increase
increase = increase.dropna()
increase_cluster_data = f(increase)[1]
percentage_increase_cluster_data = f(percentage_increase)[1]
shape_visual(percentage_increase, 'percentage increase', price)
shape_visual(increase, 'increase', price)