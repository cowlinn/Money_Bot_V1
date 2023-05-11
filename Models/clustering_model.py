import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math
import random
# rough idea for clustering model
# make a model based on time-clustering of peaks of higher order derivative percentage changes 
        # need to somehow identify clusters, whether we are in a cluster and what the next move of the cluster will be
        # the absolute values might be useful here
        # maybe have some threshold value for absolute seventh order derivative and say that if abs is above that, its in a cluster, then spaces where it drops below threshold are between clusters?
        # study higher order derivatives (maybe 3rd onwards)
# The goal of building this model is to identify ways we can characterise the fractals which make up financial data
# if we are able to generate real-looking data with certain identified characterisitcs, we can measure those same characteristics in real data
# this allows us to build a sound statistical model of price movement

#################################### NOTES ##########################################
# I focused on using the 3rd derivative of percentage_increase (percentage_pop)
# one method of cluster detection is to use some arbitrary threshold and define a function like
# def f(x):
#     x = abs(x)
#     y = []
#     for i in x:
#         if i > 1:
#             i = 1
#         else:
#             i = 0
#         y.append(i)
#     for i in range(1, (len(y)-1)):
#         if y[i] == 0 and y[i+1] == 1 and y[i-1] == 1:
#             y[i] = 1
#     for i in range(1, (len(y)-1)):
#         if y[i] == 1 and y[i+1] == 0 and y[i-1] == 0:
#             y[i] = 0
#     return y          
#
# This works decently well at finding clusters, however, the use of an arbitrary threshold means that each derivative requres a new threshold
# Also, we have no way of discerning the magnitude of each cluster from the transformed data
# but again, a separate function could be used for that


def derivative(x):
    return x - x.shift()

# cluster detection
def f(x):
    x = abs(x)
    y = []
    for i in x:
        if i > 1:
            i = 1
        else:
            i = 0
        y.append(i)
    for i in range(1, (len(y)-1)):
        if y[i] == 0 and y[i+1] == 1 and y[i-1] == 1:
            y[i] = 1
    for i in range(1, (len(y)-1)):
        if y[i] == 1 and y[i+1] == 0 and y[i-1] == 0:
            y[i] = 0
    return y            

def shape_visual(x, name): # plot the time dependence of a variable in one plot and the identified clusters in another plot
    plt.subplot(2,1,1)
    plt.plot(range(len(x)), (x))
    name = name + ' time dependence'
    plt.title(name)
    plt.subplot(2,1,2)
    plt.plot(range(len(x)), f(x))
    # f() is some function that tries to identify where clusters are located
    clust_name = "cluster detection"
    plt.title(clust_name)
    plt.tight_layout(pad=1.0)
    plt.show()

stock_name = "SPY"
data_period = "6d"
resolution = "15m"
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
# increase pd series object always has (shift) less rows than hist
# acceleration = derivative(increase)
percentage_acceleration = derivative(percentage_increase)
# jerk = derivative(acceleration)
percentage_jerk = derivative(percentage_acceleration)
percentage_crackle = derivative(percentage_jerk)
percentage_pop = derivative(percentage_crackle)
percentage_sixth = derivative(percentage_pop)
percentage_seventh = derivative(percentage_sixth)
percentage_eighth = derivative(percentage_seventh)







plt.plot(range(len(percentage_pop)), abs(percentage_pop))
plt.grid()
plt.show()






