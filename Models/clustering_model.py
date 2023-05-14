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
    # I fixed this by quantifying how far a given spike is from the mean using the SD
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
    
# by identifying when we are in a volatility cluster, we can choose different models to apply to predict price movement
# or we can have some tolerance level for volatility (for example if cluster level > 1, stop trading or start trading, depending on strategy)

# can we synthesise financial data based on points 1 2 and 3 alone? (plus mean and SD of the real data)


# model structure so far:
# - working on percentage_pop
# 1. call pmcheck() to find the probability of direction changes
# 2. 

def derivative(x):
    return x - x.shift()

def probability(probability):
    return random.random() < probability

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


# cluster detection
# NOTE: for high resolution data (1m or 2m granularity), this function is nearly useless as it picks up on noise as actual volatility
# this only works well for 5min data onwards, though it works best for 15m imo
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
    return y_smooth, y_chunky
# next step from here is to find how often different magnitudes occur? (for point 3.)
# is it more useful to use the step-wise data rather than the averaged data for this? 
# I mean I could use the local maxima of the y data and place clusters there, and that will be their magnitude and freq?
# even if a cluster is HUGE, it still is just one cluster. If a cluster has more than one peak (>1 local maxima within cluster)
# it often looks like a superposition of two  or moreclusters so I should count that as two

# first, find probability of peak occuring (done)
# then, given that a point is a peak centre, what is its magnitude? (done)
# also we should characterise the width of the peaks (this is the next step)
    # a note on the peak widths:
        # even in step-wise data (rough), the peaks still increase in a gradient with varying speeds
        # in general, shorter peaks are wider and taller peaks are narrower 
        # gotta find some way to quantify this width
        # also, they are usually (but not always) symmetric
        # when two or more peaks have widths that encroach upon each other, it doesn't look like a proper superposition
        # it looks more like the overlapping parts just have the same value (no need to add up the amplitudes)
        # lastly, the top of the peaks themselves also have different widths that we need to characterise
        # these tops may be somehow correlated with the width of the entire structer
        # we now need to figure out how to quantify the statistical behaviour of these widths
        # this will allow us to generalise our characterisation to data for any stock, across any time frame, with any granularity
# takes in cluster data (f(x))
def count_peaks(x, texture):  # counts the number of local maxima in a given set of cluster data
    if texture == 'smooth':
        texture = 0
    elif texture == 'rough':
        texture = 1
    else:
        print("Please specify texture")
        return
    peak_count = 0
    x_lst = x[texture].dropna().tolist()
    peak_coords = []
    for i in range(1, (len(x_lst)-1)):
        if (x_lst[i] > x_lst[i-1]) and (x_lst[i] >= x_lst[i+1]):
            peak_count +=1
            peak_coords.append(i)
            # print(i) # peak locations
    #print(peak_coords)
    return peak_count, peak_coords

# takes in cluster data (f(x))
def rough_peak_prob(x):   # finds the probability that a given point in cluster data is a peak-center
    x_lst = x[1].dropna().tolist()
    peak_count = count_peaks(x, 'rough')[0]
    peak_prob = peak_count/len(x_lst)
    return peak_prob  # probability of a given coordinate being a peak

# takes in cluster data (f(x))
def rough_magnitude_prob(x):
    # find max magnitude in terms of no. of SD away from the mean magnitude
    max_magnitude = x[1].max()
    mag_list = list(range(1, max_magnitude+1))   # list of all possible magnitudes
    # mag_freq_list = [0]*max_magnitude
    # total_samples = len(x[1])
    peak_data = count_peaks(x, 'rough')
    peak_coords = peak_data[1]
    num_peaks = peak_data[0]
    mag_dict = {}
    for i in mag_list:
        counter = 0
        for n in peak_coords:
            if x[1][n] == i:
                counter += 1
        mag_prob = counter/num_peaks
        mag_dict[i] = mag_prob
    #print(mag_dict)
    return mag_dict   # returns a dictionary with keys being magnitude (how many SD away from mean) and values being probability
# what this means is that if we know a peak is here, this distribution describes what its magnitude will be

# takes in some set of data (like percentage_pop)
# and tries to synthesize data that looks similar and behaves the same way statistically
def synthesise(x):
    domain = [0]*len(x)
    magnitude_distribution = rough_magnitude_prob(f(x))
    magnitude_distribution_lst = []
    # convert from dictionary to a list
    for i in magnitude_distribution:
        magnitude_distribution_lst.append(magnitude_distribution[i])
    # list of all likely magnitudes
    magnitude_lst = list(range(1, len(magnitude_distribution)+1))
    peakProbability = rough_peak_prob(f(x))
    # distribute peaks
    for i in range(len(x)):
        if probability(peakProbability):
            domain[i] = 1
    # apply magnitude distribution
    for i in range(len(x)):
        if domain[i] == 1:  # if peak, apply distribution to decide its magnitude
            domain[i] = random.choices(magnitude_lst, weights=magnitude_distribution_lst, k=1)[0]
    return pd.Series(domain)
# remarks on synthesised data:
    # the distribution looks right, but the peak widths probably need more characterising before we can start smoothing with rolling ave


def shape_visual(x, name): # plot the time dependence of a variable in one plot and the identified clusters in another plot
    y = f(x)[0]   # [0] is smoothed data, [1] is chunky data
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

def shape_synth(x, name):
    y = f(x)[1]   # [0] is smoothed data, [1] is chunky data
    plt.subplot(2,1,1)
    plt.plot(range(len(y)), (y))
    name = name + ' real data'
    plt.title(name)
    plt.grid()
    plt.subplot(2,1,2)
    z = synthesise(x)
    plt.plot(range(len(z)), z)
    clust_name = "synthesised data"
    plt.title(clust_name)
    plt.tight_layout(pad=1.0)
    plt.grid()
    plt.show()
stock_name = "SPY"
data_period = "10d"
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

shape_visual(percentage_pop, "percentage_pop")
shape_synth(percentage_pop, "percentage_pop")




# plt.plot(range(len(percentage_pop)), abs(percentage_pop))
# plt.grid()
# plt.show()

# I was testing the random python library
# seems like there can be a couple of percent difference even at 1000 trials
def prob_check(x):
    truecounter = 0
    falsecounter = 0
    for i in range(1000):
        if probability(rough_peak_prob(f(x))):
            truecounter+=1
        else:
            falsecounter +=1
    tested_prob = truecounter/(truecounter+falsecounter)
    print("Expected probability is", rough_peak_prob(f(x)), "\ntested probability is", tested_prob)
    return tested_prob


