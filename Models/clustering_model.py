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


# predictive model structure so far:
# - working on percentage_pop
# 1. call pmcheck() to find the probability of direction changes
# 2. find relavant probabilities, mean and SD to describe higher order derivative data
# 3. based on probabilities and pmcheck(), predict next change in higher order derivative (in the form of a probability distribution)
# 4. express the probability distribution in terms of price changes

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
    return y_smooth, y_chunky, rolling_window
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
    # to parse synthesised data
    if isinstance(x, list):
        peak_coords = []
        for i in range(1, (len(x)-1)):
            if (x[i] > x[i-1]) and (x[i] >= x[i+1]):
                peak_count +=1
                peak_coords.append(i)
        return peak_count, peak_coords
    # for normal data
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

# takes in cluster data(f(x))
def point_width(x):
    # goal of this function is to find a width distribution for points at different height
    x_lst = x[1].dropna().tolist()
    max_magnitude = x[1].max()
    mag_list = list(range(1, max_magnitude+1))   # list of all possible magnitudes
    peak_data = count_peaks(x, 'rough')
    peak_coords = peak_data[1]
    max_point_width = 0
    # find the maximum point width
    width_dist = {}   # dictionary that cointains a bunch of dictionaries. the keys are magnitudes, the values are width distributions for each magnitude
    # given that a peak is of magnitude i, what is the probability that its point width is w
    # count peaks of magnitude i, count points with width w, divide w count by peak count
    for i in peak_coords:
        idx = i
        point_width = 1
        while x_lst[idx] == x_lst[idx+1]:
            point_width += 1
            idx += 1
            if idx+1 == len(x_lst):
                break
        if point_width > max_point_width:
            max_point_width = point_width
    possible_widths = list(range(1,max_point_width+1)) # list of all possible widths
    for i in mag_list:
        mag_idx = i
        i = {}   # width_size (or w): probability that point has width w
        for w in possible_widths:
            peak_counter = 0 # counts how many peaks are of magnitude i
            w_counter = 0   # counts how many peaks at each magnitude in mag_idx have width of peak_width
            for n in peak_coords:
                coord_idx = n
                point_width = 1
                if x[1][n] == mag_idx:
                    peak_counter += 1
                    while x_lst[coord_idx] == x_lst[coord_idx+1]:
                        point_width += 1
                        coord_idx += 1
                        if coord_idx+1 == len(x_lst):
                            break
                    if point_width == w:
                        w_counter += 1
            if peak_counter != 0:
                # print(peak_counter, mag_idx, w_counter)
                i[w] = w_counter/peak_counter
            elif peak_counter == 0:
                i[w] = 0
        width_dist[mag_idx] = i
    return width_dist
#########################################################################################################
############################### I decided to trash this function ########################################
# takes in cluster data (f(x))
# def peak_spread(x):
#     # only peaks of magnitude > 1 have a spread (due to step-wise nature of rough data)
#     # assumptions:
#         # spreads are symmetric about peaks
#         # spreads happen in regular intervals (peak of 3 goes to 2 then to 1 or peak of 8 goes to 5 then to 1 then to 0)
#     # since in reality spreads are usually not perfectly symmetric, we will measure the largest spread for a given peak
#     # what we will measure here is far is the furtherst zero coordinate from a given peak's max value
#     # goal of this func is to find a spread distribution for each magnitude of peak
#         # is point width idependent from peak spread?? I think so
#     x_lst = x[1].dropna().tolist()
#     max_magnitude = x[1].max()
#     mag_list = list(range(1, max_magnitude+1))   # list of all possible magnitudes
#     peak_data = count_peaks(x, 'rough')
#     peak_coords = peak_data[1]
#     left_max_spread = 0
#     right_max_spread = 0
    
#     for i in mag_list:
#         if i == 1:   # only run spread checking if peak magnitdue is big enough
#             continue
#         mag_idx = i
#         i = {}
#         for n in peak_coords:
#             if x[1][n] == mag_idx:
#                 # find the largest decrease within 2 steps and that will be the spread
#                 # if the magnitude doesn't fall to 0 within 2 steps, assume it to be 0 in the next step
#                 return
        
#     return
#########################################################################################################


# takes in some set of data (like percentage_pop)
# and tries to synthesize data that looks similar and behaves the same way statistically
def synthesise(x):
    y = f(x)
    domain = [0]*len(x)
    magnitude_distribution = rough_magnitude_prob(y)
    magnitude_distribution_lst = []
    # convert from dictionary to a list
    for i in magnitude_distribution:
        magnitude_distribution_lst.append(magnitude_distribution[i])
    # list of all likely magnitudes
    magnitude_lst = list(range(1, len(magnitude_distribution)+1))
    peakProbability = rough_peak_prob(y)
    # distribute peaks
    for i in range(len(x)):
        if probability(peakProbability):
            domain[i] = 1
    # apply magnitude distribution
    for i in range(len(x)):
        if domain[i] == 1:  # if peak, apply distribution to decide its magnitude
            domain[i] = random.choices(magnitude_lst, weights=magnitude_distribution_lst, k=1)[0]
    # apply point width distribution
    width_distribution = point_width(y)
    width_list = list(range(1, len(width_distribution[1])+1))  # all possible point widths
    peak_coords = count_peaks(domain, 'rough')[1]
    # print(peak_coords)
    # print(domain)
    for i in magnitude_lst:
        w_dist = width_distribution[i]# width probability distribution for a given magnitude i
        w_dist_lst = [] 
        for a in w_dist:
            w_dist_lst.append(w_dist[a])
        for n in peak_coords:
            if domain[n] == i:
                # assign a width to each point based on its magnitude
                width = random.choices(width_list, weights=w_dist_lst, k=1)[0]
                idx = 1
                if n+width > len(domain):
                    excess = n+width - len(domain)
                    width = width - excess
                while width > 1:
                    domain[n+idx] = domain[n]
                    idx += 1
                    width -=1
                # add right side spread
                if n+width+1<len(domain):
                    if i > 1 and domain[n+width+1] == 0:
                        if probability(0.75):  # right side spread is rarer than left side
                            domain[n+width+1] = math.ceil(domain[n]/2)
                            if n+width+2<len(domain) and probability(0.25):
                                domain[n+width+2] = math.ceil(domain[n]/4) # small chance of fat right tail
    # add left side spread
    for n in peak_coords:
        if n>1:
            if domain[n] > 1 and domain[n-1] == 0:
                if probability(0.90):  # left side spread is fairly common
                    domain[n-1] = math.ceil(domain[n]/2)
                    if n>2 and probability(0.40):
                        domain[n-2] = math.ceil(domain[n]/4)
    
                
    return pd.Series(domain)
    
#######################################  FULL NOTES ON SYNTHESIS #########################################
# What have I learnt from synthesising market data?
# it seems that we can fully describe the statistical behaviour of higher order derivatives of price to produce comvincing mock data
# of course, the pseudorandom functions are not actually that accurate (try using the prob_checker() function to test)
# this will mean that the distributions are usually not prcise when synthesising.
# there seem to be 3 main things we need to know in order to describe a set of  volatility clustering data
    # 1. the probability that a given coordinate is a peak (can be obtained via rough_peak_prob() function)
    # 2. the magnitude probability distribution of a peak, given that point is a peak (can be obtained via rough_magnitude_prob() function)
    # 3. the width of the tip of a peak, given that peak is of a certain magnitude (can be obtained via point_width())
    
    # as for spread, I decided that it wasn't worth figuring out a probability distribution for that.
    # by observation, I noticed each step away from the peak's top had the effect of approximately halving the value
    # and some peaks had longer tails, while others had no tails so I added some probabilistic factors in the synthesise() function to simulate this
#
# the synthesis function basically applies all 3 points by measuring the key probabilities from the actual data
# it then applies some spread (that can be changed manually if desired) 
# We end up with a set of fake data that both looks visually similar and behaves statistically identically to the original data
#
# What are the next possible steps from here?
# I think there are 3 main possibilities.
#
# 1. develop a predictive model (according to the structure above) using the following steps:
    # 1. call pmcheck() to find the probability of direction changes
    # 3. based on probabilities and pmcheck(), predict next change in higher order derivative (in the form of a probability distribution)
    # 4. express the probability distribution in terms of price changes


# 2. use the cluster identification function f() to figure out when we are in a volatility cluster and figure out the likely direction using pmcheck()
# ok the pmcheck() for direction may be a stretch but it's a thought
# basically if for example we develop strategies for high volatility periods, we want to know objectively when we are in a high volatility period
# the f() function can already augment other models by quantifying volatility to decide whether we should even be using a given model
# there are options strategies which love high volatility and those which love low volatility so this can also be useful for choosing between those strats
# beyond just quantifying current volatility, we can also know the statistical behaviour of a given stock/equity's volatility
# this alone can help us decide which options strategies to us


# 3. attempt to use fractal mathematics to perform fractal analysis
    # for this, I need to read more about statistical fractals in time, how to do math with them and whether this is actually applicable here
    # but the rough idea is based on the following points:
        # 1. stock market price changes are a fractals in time - the charts look the same regardless of time scale/resolution
        # 2. the statistical properties are also largely unchanged across timescales
        # 3. we can exploit this fact by analysing super long time scales to get more accurate results, then applying those results to more reasonable timescales for a predictive model (like option 1)
        # 4. alternatively, we can use results from analysing moderate time scales to day trade options
        # 5. OR, we can aggregate results ACROSS time scales for long-term positions
    # there are probably more things we can do with fractal maths but idk
##########################################################################################################    

# predict the next value of x
def rough_predict(x):
    y = f(x)  # rough cluster data
    y_lst = y[1].tolist()
    flip_prob = pmcheck(x)
    mean = x.mean()
    SD = x.std()
    peak_prob = rough_peak_prob(y)   # probability that the next point is a peak
    magnitude_dist = rough_magnitude_prob(y)   # if it is a peak, describe its magnitude 
    width_dist = point_width(y)     # how long will the peak last for?
    
    possible_magnitudes = list(range(1, len(magnitude_dist)+1))
    possible_widths = list(range(1, len(width_dist[1])+1))
    
    latest_y_val = y_lst[-1]
    second_latest_y_val = y_lst[-2]
    
    if latest_y_val == 0:   # if no cluster
        final_distribution = {}
        for i in possible_magnitudes:
            mag = i
            i = {}
            for w in possible_widths:
                i[w] = peak_prob*magnitude_dist[mag]*width_dist[mag][w]
            final_distribution[mag] = i
        return final_distribution  # final distribution of potential peaks (case for no peak is not shown. that should just be  1 - sum of all probabilities in the final dist)
    # first set of key:value pairs is magnitude:(dictionary containing width probabilities for that magnitude)
    # second set of key:value pairs is always width:probability
    # in effect, to get to probability of the next data point being a peak of magnitude 1, width 1
    # you would take final_distribution[1][1]
    # for magnitude 2 width 1 it would be final_distribution[2][1]
    # for magnitude 3 width 2 it would be final_distribution[3][2] and so on
    # this will be the format for the output of this function
            

    # find out if we are in a cluster of some kind
    if latest_y_val > 0 and second_latest_y_val > latest_y_val:  # exiting a cluster/ tail end of a cluster
        return
    
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

# synthesise rough data and compare with real rough data
def shape_synth(x, name):
    y = f(x)[1]   # [0] is smoothed data, [1] is chunky data
    max_y = y.max()
    plt.subplot(2,1,1)
    plt.plot(range(len(y)), (y))
    name = name + ' real data'
    plt.title(name)
    plt.grid()
    plt.ylim(0, max_y+0.25)
    plt.subplot(2,1,2)
    z = synthesise(x)
    plt.plot(range(len(z)), z)
    clust_name = "synthesised data"
    plt.title(clust_name)
    plt.tight_layout(pad=1.0)
    plt.grid()
    plt.ylim(0, max_y+0.25)
    plt.show()

# synthesise rough data, smooth it and compare with real smooth data
def smooth_shape_synth(x, name):
    complete_y_data = f(x)
    y = complete_y_data[0]   # [0] is smoothed data, [1] is chunky data
    max_y = y.max()
    plt.subplot(2,1,1)
    plt.plot(range(len(y)), (y))
    name = name + ' real data'
    plt.title(name)
    plt.grid()
    plt.ylim(0, max_y+0.25)
    plt.subplot(2,1,2)
    z = synthesise(x)
    smooth_z = z.rolling(complete_y_data[2]).mean()
    plt.plot(range(len(smooth_z)), smooth_z)
    clust_name = "synthesised data"
    plt.title(clust_name)
    plt.tight_layout(pad=1.0)
    plt.grid()
    plt.ylim(0, max_y+0.25)
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
smooth_shape_synth(percentage_pop, "percentage_pop")



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


