import datetime
import os
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math
import random
# import schedule
import time

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

# we can use the expect() function to judge how good the brainded strategy is wrt a given stock
# for example expect(increase, -2) on MSFT returns -5.032 (good correlation, suggests that brainded strat works)
# while expect(increase, -2) on TSLA returns 5.812 (bad correlation, do no use the strat)
# it can also help us determine which magnitdues are actually useful in a given stock
# for example expect(increase, 1) on MSFT returns 2.432 (good) while expect(increase, -1) on MSFT returns 0.678 (bad)
def expect(x, current_val = 3):  # what cluster value do you want info for?
    x_lst = x.tolist()
    cluster_data = f(x)[1]
    cluster_lst = cluster_data.tolist()
    if current_val == 'latest':
        print('The latest cluster value is', cluster_lst[-1])
        current_val = cluster_lst[-1]
    sample_size = 0
    total = 0
    for i in range(len(cluster_data)-1):
        # for non-zero current_val (cluster values)
        # I thought about using >= for cluster_data[i] here, but I would have to deal with 'positive' zero and 'negative' zero cases
        # so nvm ah
        # also this would be misleading because directional magnitude of 3 means something diff from magnitude of 5
        # if current_val > 0 and cluster_data[i] >= current_val:  
        #     sample_size += 1
        #     total += x_lst[i+1]
        # elif current_val < 0 and cluster_data[i] <= current_val:
        #     sample_size += 1
        #     total += x_lst[i+1]
        
        if cluster_data[i] == current_val:  
            sample_size += 1
            total += x_lst[i+1]

        # usually current_val only == 0 if 'latest' is requested
        # for 'positive' zeros
        # if current_val == 0 and x_lst[-1] > 0:
            
    # NOTE: current_val = 0 usually does not returna useful result
    # use expect(x, 'latest') with caution
    print('Sample size is', sample_size)  # sample size of ~50 is ideal
    if sample_size == 0:
        print('No valid occurences of this cluster magnitude for given historical range')
        return
    expected_next_val = total/sample_size
    # might want to return sample size and current_val if we are going to use this in another function
    # makes it easier for computer to evaluate usefulness of information from this function
    # but anyway sample size for non-zero stuff is usually small so wtv
    return expected_next_val # expected next value of x
    # also, if expected_next_val is close to zero, info is p much useless in terms of directionality

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

stock_name = "MSFT"
data_period = "10d"
resolution = "15m"
time_interval = 1
shift = int(time_interval) # converts time interval into however many 15 min blocks. Note that there are 6.5 trading hours in a trading day
# formula for 1d resolution and for all integer time interval is int(time_interval)
# formula for 1h resolution and integer day time interval is int(time_interval*7)
# formula for 15m resolution and 1 day time interval is int(time_interval*6.5*4)
# formula for 15m resolution and 1h time interval (=1) is int(time_interval*4)
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
expect(increase, 'latest')

## for visualization purposes, put them next to each other on a CSV
curr_day_to_string = datetime.date.today()
def get_offset(cluster, os_length):
    l = [-69 for i in range(os_length)] #-69 is an arbitrary int value for offset
    ratio = cluster.tolist()
    vals = l + ratio
    #new_offset_c = pd.concat((pd.DataFrame(l), cluster), axis = 0).reindex() #concat row_wise
    index = [i for i in range(len(vals))]

    new_offset_c = pd.DataFrame({
        'y': index,
        'Clusters': vals
    }, index=index)
    return new_offset_c

increase_cluster_data_os = get_offset(increase_cluster_data, os_length=shift)

cache_fname = "../historical/" + f"{stock_name}_compare_directional_{curr_day_to_string}.csv"
mega_chart = pd.concat((price, increase_cluster_data_os), axis=1)[["Close", "Clusters"]]

mega_chart.to_csv(cache_fname) 

def main(stock_name, data_period, resolution, shift):
    stock = yf.Ticker(stock_name)  # this goes in main()
    hist = stock.history(period = data_period, interval = resolution) # historical price data
    price = hist['Close']
    increase = price - price.shift(shift)
    increase = increase.dropna()
    increase_cluster_data = f(increase)[1]
    prediction = expect(increase, 'latest')
    if prediction > 0:
        return 1, increase
    else:
        return -1, increase

iteration_counter = 0
record = []  # after letting the program run to completion, we should have a list of all prediction results
# and we can do sum(records)/len(records) to find the winrate
buffer = 0
while True:
    now = datetime.datetime.now()
    if now.minute%15 == 0 and now.second == 1:
        print(now)
        time.sleep(0.7)
        info = main(stock_name, data_period, resolution, shift)
        increase_lst = info[1].tolist()
        if buffer == increase_lst[-1]: # if the last coord was the same, trading has ended
            break
        if iteration_counter == 0:  # for first prediction
            prediction = info[0]
            iteration_counter += 1
            print('This is iteration 1')
            time.sleep(0.4)
            continue
        if prediction > 0 and increase_lst[-1] > 0:
            record.append(1)
            print('Good prediction!')
            prediction = info[0] # make a new prediction
        elif prediction < 0 and increase_lst[-1] < 0:
            record.append(1)
            print('Good prediction!')
            prediction = info[0]
        else:
            losses = random.randrange(1,69000000)
            record.append(0)
            print('Bad prediction! You lost', losses, 'tendies!')
            prediction = info[0]
        iteration_counter += 1
        print('This is iteration', iteration_counter)
        buffer = increase_lst[-1]
        time.sleep(0.4)

        
        
            
        