import datetime
import os
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math
import random
import clustering_model as clst


def directional(x): # increase
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

def volatility(x):
    x = abs(x).dropna()
    x_lst = x.tolist()
    y = []
    for i in x:
        if i > x.mean():
            i = 1
        else:
            i = 0
        y.append(i)

    for i in range(1, (len(y)-1)):
        magnitude = 1
        while x_lst[i] > (x.mean() + magnitude*x.std()):
            y[i] += 1
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

def derivative(x):
    return x - x.shift()
def ordered_derivative(x, order):
    while order > 0:
        x = derivative(x)
        order -= 1
    return x

def pm_optimise(x, threshold): # finds the optimal derivative (highest output of pmcheck()) and returns that derivative
# note: should take in percentage_increase pd series
    order = 0
    while clst.pmcheck(ordered_derivative(x, order)) < threshold and len(ordered_derivative(x, order).dropna()) > math.ceil(0.7*len(x)) and order<4:  # finds the derivative that meets a threshold value
        order +=1
    print(str(order)+"th derivative")
    y = ordered_derivative(x, order)
    print(clst.pmcheck(y))
    return y, order  # y is the first derivative that returns a pmcheck that is greater than the next derivative

def shape_visual(price): # plot the time dependence of a variable in one plot and the identified clusters in another plot
    x = derivative(price).dropna()
    y = volatility(pm_optimise(x, 0.95)[0])[0]   # [0] is smoothed data, [1] is chunky data
    y1 = directional(x)[0]
    plt.subplot(3,1,1)
    plt.plot(range(len(y)), (y))
    name = 'volatility clustering'
    plt.title(name)
    plt.tight_layout(pad=1.0)

    plt.grid()
    plt.subplot(3,1,2)
    plt.plot(range((len(y1)-len(y)), len(y1)), y1[(len(y1)-len(y)):])
    # f() is some function that tries to identify where clusters are located
    clust_name = "directional clustering"
    plt.title(clust_name)
    plt.tight_layout(pad=1.0)
    plt.grid()
    plt.subplot(3,1,3)
    plt.plot(range((len(price)-len(y)), len(price)), price[(len(price)-len(y)):])
    # f() is some function that tries to identify where clusters are located
    clust_name = "price"
    plt.title(clust_name)
    plt.tight_layout(pad=1.0)
    plt.grid()

    plt.show()
    
stock_name = "GOOGL"
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

