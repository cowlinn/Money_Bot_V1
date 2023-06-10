import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math
import random
import clustering_model_test as clst


# this model assumes that each clustering data point is dependent on the previous point(s)
# it asks the question of "given that this point is of magnitude m, what is the probability of the next point being magnitude n?"
# since we don't need the complete distributions, the prediction algo will only find the probability distribution for magnitdue m

# it may be worth expanding this to more prior points?

######################################  NOTES #################################################
# this model seems to work rather poorly with boring data and outlier data
# boring meaning there's no 'signature' for it to pick up on, outlier means the pattern is TOO unique
# a sequence of 000 vs 111 vs 012 vs 015 have increasing order of 'spiciness'
# for boring stuff like a sequence of 3 zeros, there's so many occurences of it (for example a sequence of 5 zeroes alone has 3 instances of 000)
# this makes it really difficult to predict what the next number will be
# to get around this, we can increase the prediction length (for example to last 5 coords, then a sequence of 5 zeroes only registers as 1 instance)
# however, the more we increase the length, the less reliable and statistically significant
# our predictions for more unique sequences becomes
# maybe we can have some way to determine what the ideal prediction length for a sequence will be?
# how can we quantify complexity of a sequence?
# maybe something like while sample size < 50, reduce pred length and try again?

# note on magnitude:
    # based on the f() function, a magnitude of 1 just means it's greater than the average magnitude (abs(x).mean())
    # a magnitude of 2 means it is greater than the mean magnitude plus one abs(x).std()
    # every magnitude up adds one SD

# note on limits of the model:
    # the model requires a particular type of resolution/data period/interval
    # for example it doesn't work with 1d resolution, 2y timeperiod and 1 time interval?
    # this might be an issue with overfitting
    # because the pmcheck for lower derivatives is only about 80%, our predictions will be wrong 20% of the time

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

# given that the current magnitude is m what is the probability distribution of the magnitude of the next coordinate?
# takes in raw data
def predict1(x):
    y = clst.f(x)   # cluster data
    y_lst = y[1].tolist()
    max_magnitude = y[1].max()
    mag_list = list(range(0, max_magnitude+1))   # list of all possible magnitudes (including 0)
    latest_mag = y_lst[-1]    # last known magnitude
    # peak_coords = clst.count_peaks(y, 'rough')[1]
    next_mag_count = {}
    for i in mag_list:
        next_mag_count[i] = 0
    for i in range(len(y_lst)-1):
        if y_lst[i] == latest_mag:
            next_mag = y_lst[i+1]
            next_mag_count[next_mag] += 1
    total_count = sum(next_mag_count.values())
    print('sample size is', total_count)
    final_magnitude_distribution = next_mag_count.copy()
    for i in final_magnitude_distribution:
        final_magnitude_distribution[i] = final_magnitude_distribution[i]/total_count
    return final_magnitude_distribution
            
# given that the current magnitude is m and the previous magnitude is n, what is the probability distribution of the next coordinate?
# this probably requires A LOT more historical data (since it is counting occurences of a sequential event)
# takes in raw data
def predict2(x):
    y = clst.f(x)   # cluster data
    y_lst = y[1].tolist()
    max_magnitude = y[1].max()
    mag_list = list(range(0, max_magnitude+1))   # list of all possible magnitudes (including 0)
    latest_mag = y_lst[-1]    # last known magnitude
    previous_mag = y_lst[-2]
    next_mag_count = {}
    for i in mag_list:
        next_mag_count[i] = 0
    for i in range(1, len(y_lst)-1):
        if y_lst[i] == latest_mag and y_lst[i-1] == previous_mag:
            next_mag = y_lst[i+1]
            next_mag_count[next_mag] += 1
    total_count = sum(next_mag_count.values())
    print('sample size is', total_count)
    final_magnitude_distribution = next_mag_count.copy()
    for i in final_magnitude_distribution:
        final_magnitude_distribution[i] = final_magnitude_distribution[i]/total_count
    return final_magnitude_distribution

# given that the current magnitude is m and the previous magnitude is n and the one before that is of magnitude o, what is the probability distribution of the next coordinate?
# this probably requires EVEN MORE historical data (since it is counting occurences of a longer sequential event)
# there's definitely diminishing returns here in terms of accuracy (based on reduction in sample size)
# at which point do we run into the problem of overfitting?
# based on preliminary testing, it seems that at predict3(), the majority conclusion still makes sense (greatest probability outcome)
# However, due to the small sample size, the smaller probability outcomes start to become weird
# takes in raw data
def predict3(x):
    y = clst.f(x)   # cluster data
    y_lst = y[1].tolist()
    max_magnitude = y[1].max()
    mag_list = list(range(0, max_magnitude+1))   # list of all possible magnitudes (including 0)
    latest_mag = y_lst[-1]    # last known magnitude
    second_latest_mag = y_lst[-2]
    third_latest_mag = y_lst[-3]
    next_mag_count = {}
    for i in mag_list:
        next_mag_count[i] = 0
    for i in range(2, len(y_lst)-1):
        if y_lst[i] == latest_mag and y_lst[i-1] == second_latest_mag and y_lst[i-2] == third_latest_mag:
            next_mag = y_lst[i+1]
            next_mag_count[next_mag] += 1
    total_count = sum(next_mag_count.values())
    print('sample size is', total_count)
    final_magnitude_distribution = next_mag_count.copy()
    for i in final_magnitude_distribution:
        final_magnitude_distribution[i] = final_magnitude_distribution[i]/total_count
    return final_magnitude_distribution

# generalised to accept varying prediction lengths
def predict(x, pred_length):
    y = clst.f(x)   # cluster data
    y_lst = y[1].tolist()
    max_magnitude = y[1].max()
    mag_list = list(range(0, max_magnitude+1))   # list of all possible magnitudes (including 0)
    latest_mag = y_lst[-1]    # last known magnitude
    sequence = y_lst[-pred_length:]  # use the last (pred_length) values as the sequence to find
    next_mag_count = {}
    for i in mag_list:
        next_mag_count[i] = 0
    for i in range(pred_length-1, len(y_lst)-1):
        if y_lst[i] == latest_mag and y_lst[i-(pred_length-1):i+1] == sequence:
            next_mag = y_lst[i+1]
            next_mag_count[next_mag] += 1
    sample_size = sum(next_mag_count.values())
    # print('sample size is', sample_size)
    if sample_size == 0:  # prevent division by 0 errors
        placeholder = {}
        return placeholder, sample_size
    final_magnitude_distribution = next_mag_count.copy()
    for i in final_magnitude_distribution:
        final_magnitude_distribution[i] = final_magnitude_distribution[i]/sample_size
    return final_magnitude_distribution, sample_size

# predict the next value of a set of data
def optimised_predict(x, minimum_sample_size, min_pred_length = 3):
    pred_length = math.ceil(0.02*(len(x.dropna().tolist())))  # start with 2% of the data. we do not want to  have a pred_length too short
    iteration_counter = 0
    while predict(x, pred_length)[1] < minimum_sample_size and pred_length > min_pred_length:
        # print('current pred length is', pred_length, 'current sample size is', predict(x, pred_length)[1])
        pred_length -= 1
        iteration_counter += 1
    prediction = predict(x, pred_length)
    if prediction[1] < minimum_sample_size:
        print("WARNING: SAMPLE SIZE MAY BE TOO SMALL FOR MINIMUM PREDICTION LENGTH OF", min_pred_length)
    print(iteration_counter, "iterations to optimise")
    print("prediction length of", pred_length, "required for sample size of", prediction[1])
    return prediction[0]

# hypothesis 1: the quantity will move in the direction of its mean/meadian (if > mean, move down, if < mean, move up)
    # about 90% success rate, better than using pmcheck() to determine direction
def hypo_tester1(x):
    if isinstance(x, list):
        x = pd.Series(x).dropna()
        x_lst = x.tolist()
    x_lst = x.dropna().tolist()
    equilibrium = x.mean()
    win_counter = 0
    loss_counter = 0
    for i in range(len(x_lst)-1):
        if x_lst[i] > equilibrium and x_lst[i+1]<x_lst[i]:
            win_counter += 1
        elif x_lst[i] < equilibrium and x_lst[i+1] > x_lst[i]:
            win_counter += 1
        else:
            loss_counter += 1
    # print(win_counter+loss_counter)
    return win_counter/(loss_counter+win_counter)

# hypothesis 2: if the magnitude of the quantity is at least one SD away from the mean, it will always move towards mean (otherwise we would see insane spikes)
    # always true, but only ~45 trials (means this does not account for the majority of cases)
    # but if we predict the next point to be a non-zero in magnitude, this is a good way to get direction
    # how to upgrade this to account for cases within 1 SD of the mean?
def hypo_tester2(x):
    x_lst = x.dropna().tolist()
    equilibrium = x.mean()
    SD = x.std()
    win_counter = 0
    loss_counter = 0
    for i in range(len(x_lst)-1):
        if x_lst[i] > (equilibrium+SD) and x_lst[i+1] < x_lst[i]:
            win_counter += 1
        elif x_lst[i] < (equilibrium-SD) and x_lst[i+1] > x_lst[i]:
            win_counter += 1
        if x_lst[i] > (equilibrium+SD) and x_lst[i+1] > x_lst[i]:
            loss_counter += 1
        elif x_lst[i] < (equilibrium-SD) and x_lst[i+1] < x_lst[i]:
            loss_counter += 1
    print(win_counter+loss_counter)
    return win_counter/(loss_counter+win_counter)

def hypo_tester3(x):
    absx = abs(x).dropna()
    absx_lst = absx.tolist()
    x_lst = x.dropna().tolist()
    equilibrium = absx.mean()
    mean = x.mean()
    SD = x.std()
    win_counter = 0
    loss_counter = 0
    for i in range(len(x_lst)-1):
        if x_lst[i] > 0:
            if absx_lst[i] > equilibrium and x_lst[i+1] < 0:
                win_counter += 1
            elif absx_lst[i] < equilibrium and x_lst[i] > mean and x_lst[i+1] < x_lst[i]:
                win_counter += 1
            elif absx_lst[i] < equilibrium and x_lst[i] < mean and x_lst[i+1] > x_lst[i]:
                win_counter += 1
            else:
                loss_counter += 1
        if x_lst[i] < 0:
            if absx_lst[i] > (equilibrium) and x_lst[i+1] > 0:
                win_counter += 1
            elif absx_lst[i] < equilibrium and x_lst[i] > mean and x_lst[i+1] < x_lst[i]:
                win_counter += 1
            elif absx_lst[i] < equilibrium and x_lst[i] < mean and x_lst[i+1] > x_lst[i]:
                win_counter += 1
            else:
                loss_counter += 1
        
    print(win_counter+loss_counter)
    return win_counter/(loss_counter+win_counter)

# conclusion from hypothesis tests:
    # it's easier and more useful to just use pm_optimised() to find some higher order derivative the flips sign 95% of the time or something


# x is the original data (like percentage price_increase)
# final_data is the higher order derivative data, with the prediction point appended at the end
# both should be pd.Series() objects
# order is how many times the original data was differentiated
# returns the original data with predicted term for orignal data appended
# basically converts a prediction for a derivative to a prediction for the original
# val
def anti_derivative(x, final_data, val = False):
    order = 0
    copy_x = x.copy()
    x_lst = x.tolist()
    final_data_lst = final_data.tolist()
    # find what order derivative is the final data
    while x_lst[-20:] != final_data_lst[-21:-1]:
        order += 1
        x = derivative(x)
        x_lst = x.tolist()
    # print(order)
    pred_x_term = final_data_lst[-1]
    while order > 0:
        # print(order)
        add_val = ordered_derivative(copy_x, order-1).tolist()[-1]
        # print(add_val)
        pred_x_term += add_val
        order -= 1
    if val:
        return pred_x_term
    pred_x_data = copy_x.tolist()
    pred_x_data.append(pred_x_term)
    pred_x_data = pd.Series(pred_x_data)
    return pred_x_data

# next steps:
    # how to turn magnitude predictions into actual data predictions?
    # what does one SD in higher order derivatives translate to? atm I think it translates to about 0.1% for the 15min timeframe


# how useful is it, really, to predict the next magnitude of something?
# usually for options, the direction is more important than the magnitude right?
# how can we characterise the directional information?
# direction information is in the derivative of a quantity
def directional_predict(x):
    return

# convert from magnitudes to actual absolute value changes
# gives a probability that the quantity studied will change by x amount for each probability
# x is the prediction quantity
# returns a dictionary where the keys are the actual maximum change values of quantity x and the values are the probabilities of them occuring
def interpreter(x, magnitude_distribution):
    positive = False
    if x.tolist()[-1] > 0:
        positive = True
    absx = abs(x).dropna()
    mag_list = list(range(len(magnitude_distribution)))   # list of all possible magnitudes (including 0)
    # magnitude 0 is greater than 0 but less than mean
    # magnitude 1 is greater than the mean but less than SD+mean
    # magnitude 2 is greater SD+mean but less than 2*SD+mean
    mean = absx.mean()
    SD = absx.std()
    # absolute_val_range_distribution = {}
    # abs_val_list = []
    max_val_list = []
    for i in mag_list:
        if i == 0:
            max_val = mean
            min_val = 0
        else:
            max_val = mean + i*SD
            min_val = max_val - SD
        # abs_val_list.append(str(round(min_val, 4)) + ' to ' + str(round(max_val, 4)))
        max_val_list.append(round(max_val, 4))
    if positive:
        for i in range(len(max_val_list)):
            max_val_list[i] = -max_val_list[i]
    # counter = 0
    # for i in abs_val_list:
    #     counter += 1
    #     subcounter = 0
    #     for n in magnitude_distribution:
    #         absolute_val_range_distribution[i] = magnitude_distribution[n]
    #         subcounter += 1
    #         # print(counter, subcounter)
    #         if counter == subcounter:
    #             # print('break', absolute_val_range_distribution)
    #             break
    counter = 0
    max_val_range_distribution = {}
    for i in max_val_list:
        counter += 1
        subcounter = 0
        for n in magnitude_distribution:
            max_val_range_distribution[i] = magnitude_distribution[n]
            subcounter += 1
            # print(counter, subcounter)
            if counter == subcounter:
                # print('break', absolute_val_range_distribution)
                break
    zero_lst = [] # list of all outcomes with 0 probability
    for i in max_val_range_distribution:
        if max_val_range_distribution[i] == 0:
            zero_lst.append(i)
    for i in zero_lst:
        del max_val_range_distribution[i]  # only return non-zero outcomes
    return max_val_range_distribution   # the maximum that x will change by
# maybe should also return the minumum?

def anti_derivative_interpreter(x, dx, max_val_distribution):
    dx_lst = dx.tolist()
    reference_dict = max_val_distribution.copy()
    # possible_outcomes = []
    max_x_distribution = {}
    for i in reference_dict:
        buffer = dx_lst.copy()
        buffer.append(i)
        # return(buffer)
        new_val = anti_derivative(x, pd.Series(buffer), val = True)
        max_x_distribution[new_val] = reference_dict[i]
    return max_x_distribution
        
        
        

def main():
    stock_name = "ADSK"
    data_period = "30d"
    resolution = "1h"
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
    dx = pm_optimise(percentage_increase, 0.95)[0]    # some higher order derivative with minimum pmcheck() of 0.95
    flip_prob = clst.pmcheck(dx)
    predicted_magnitude_distribution = optimised_predict(dx, 50, min_pred_length=2)
    max_val_distribution = interpreter(dx, predicted_magnitude_distribution)
    predicted_percentage_increase_dist = anti_derivative_interpreter(percentage_increase, dx, max_val_distribution)
    # not sure what to do at this point?
    # if we just take the highest probability prediction,the magnitude is more or less right (for appropriate data)
    # but the direction can be wrong fairly often
    
    
    # temporary
    return(predicted_percentage_increase_dist)


x = main()
print(x)
print(sum(x.values()))
### prediction = 4th derivative (acc)
### percentage chance to change 
### keys = %change, values = % chance it will happen 
## 0 <--> 0.04 * increase = 57.9%
## 0.04 time increase <--> 0.71time increase = 26.315%
## 0.71 increase <-->1.3779 increase = 5% chance
## 1.3779 <--> 2.04408 increase = 1% chance