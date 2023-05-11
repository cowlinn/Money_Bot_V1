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
#   # I ended up using i > x.mean()
# Also, we have no way of discerning the magnitude of each cluster from the transformed data
# but again, a separate function could be used for that
# spikes (volatility clusters) in higher order derivative signal volatility in the price
#   # for further refinements, it might be worth looking at the direction (by taking the absolute value in the clustering func, we do not have directional data)
#   # thus, it is probably a good idea to combine the clustering data with the percentage increase data again to predict direction on top of magnitude
#   # alternatively, we could use the pmcheck function to give a probability of when direction is likely to reverse in higher order derivatives
#   # then work backwards to find price change magnitude + direction


# so far what are the things that define a given set of data?
# 1. pmcheck - how often does the value of the series cross the zero line?  (direction of higher oder derivatives)
    # strictly speaking, what is the probability that the next value in the series has a flipped signed from the latest value?
# 2. clusters - how are volatility clusters distributed and what is their magnitude?  (magnitude of higher order derivatives)
    # currently, I have two models that are meant to trade either within or outside of clusters
    # might be worth looking at models that predict prices at cluster boundaries
    # for now, we can say that any data point with magnitude less than the average magnitude is not in a volatile cluster
# 3. cluster frequency and patterns (for this we probably need to look at a different timescale and apply it to small scale)
    # no idea how to handle this yet
    
    
# model structure so far:
# - working on percentage_pop
# 1. call pmcheck() to find the probability of direction changes
# 2. 

def derivative(x):
    return x - x.shift()

def pmcheck(x): # check how often the values of a series oscillate between positve and negative
    if isinstance(x, list):
        x = pd.Series(x).dropna()
        x_lst = x.tolist()
    x_lst = x.dropna().tolist()
    right = 0
    wrong = 0
    for i in range(len(x_lst)-1):
        if x_lst[i]>0 and x_lst[i+1]<0:
            right += 1
        elif x_lst[i]<0 and x_lst[i+1]>0:
            right +=1
        else:
            wrong +=1
    return right/(right+wrong)

def weight(x): # weight function. x is time coordinate.
# the further away a data point is in from the current time coord, the larger the x value
# x is in integers starting from x = 0 being the latest trade time
    w = 1/4*(3*math.exp(-(0.1*x)**2) + 1/(0.1*x+1))
    return w

# cluster detection
def f(x):
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
        if y[i] == 0 and y[i+1] == 1 and y[i-1] == 1:
            y[i] = 1
    for i in range(1, (len(y)-1)):
        if y[i] == 1 and y[i+1] == 0 and y[i-1] == 0:
            y[i] = 0
    for i in range(1, (len(y))):
        if x_lst[i] > (x.mean() + x.std()):   # identify different levels of volatility
            y[i] += 1
    for i in range(1, (len(y))):
        if x_lst[i] > (x.mean() + 2*x.std()):
            y[i] += 1
    for i in range(1, (len(y))):
        if x_lst[i] > (x.mean() + 3*x.std()):
            y[i] += 1
    for i in range(1, (len(y))):
        if x_lst[i] > (x.mean() + 4*x.std()):  # identify the max points if we want to scale the data later
            y[i] += 1
    
    y = pd.Series(y).rolling(4).mean()
    # now take rolling average?
    # this kind of helps to smooth out the cluster graph but it doesn't really help to identify cluster boundaries?
    
    return y            

def shape_visual(x, name): # plot the time dependence of a variable in one plot and the identified clusters in another plot
    y = f(x)
    plt.subplot(2,1,1)
    plt.plot(range(len(x)), (x))
    name = name + ' time dependence'
    plt.title(name)
    plt.grid()
    plt.subplot(2,1,2)
    plt.plot(range(len(y)), y)
    # f() is some function that tries to identify where clusters are located
    clust_name = "cluster detection"
    plt.title(clust_name)
    plt.tight_layout(pad=1.0)
    plt.grid()
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






