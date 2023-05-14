import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math
import random
########################################## NOTES ####################################################
# weighted model
# assign some weight value to each data point in historical data period, and take weighted average
# weight function is given by f(x) and can be changed here (must be finite at x = 0)
#    # the function I used was just constructed by me
#    # it assigns more significance to points closer to the most recent change
#    # this means that this model's performance close to clustered volatility is likely to be horrible
#    # so right before or right after a cluster of volatility performance is probably bad
#    # however, within clusters of volaitlity themselves and during calm periods, performance is likely to be better
#    # my next model will probably exploit clustered volatility, combined with some weighted averaging to predict price movment
#
# I used a derivative that was found to flip signs between each data point 80% of the time so I can use a negative sign in the final averaged magnitude to mimick this behaviour
# however since this only occurs a certain percentage of the time, we only want to flip the sign a certain percentage of the time
# lower derivatives gave between 46% and 77% meaning at best, the lowest derivative did not flip signs 54% of the time
# This allows us to have some prediction of the seventh order derivative, from which lower orders can be estimated to give a prediction of price


###############################################
# for replicating market data:
    
# seventh_lst = percentage_seventh.dropna().tolist()    
# seventh_lst.append(predict(seventh_lst))
# plt.plot(range(len(seventh_lst)), seventh_lst)
###############################################

# running the last two lines of code again and again makes the code predict future data based on its past prediction
# from the results, the frequency or probability of inversion seems to be appropriate.
# this indicates that this frequency is likely one of the fractal "rules"
# however, the relatively stagnant magnitude and lack of clustered volatility could be improved in the next model
# maybe we can try to find probability of a move of each magnitude in clusters to do that?
# the whole idea behind this is that if we can reproduce market data, this puts us one step closer to using fractal geometry
# it also brings us closer to being able to accurately describe the statistical behaviour of a given security
# upon further testing, it seems that we should always flip the value of the weighted average as compared to the previous data point
# this is to avoid some ridiculous result from occuring
# also, the probabilities just work out better if we flip every time
# because of that, we just have to make sure the threshold for probability of flipping is reasonably high

# I'm not sure why, but this model doesn't perform that well on SPY
# there are also issues with using too much or too little historical data, too high or too low resolution
# the model just spits out some unreasonably large price movement
# also note that RMSE is a bit high for now bc I suck at coding
######################################################################################################

######################################################################################################
## Constants ##
AAPL = "AAPL"
SnP_500 = "SPY"
eight_days = "8d"
two_months = "2mo"
default_res = "[1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]"

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

def weight(x): # weight function. x is time coordinate.
# the further away a data point is in from the current time coord, the larger the x value
# x is in integers starting from x = 0 being the latest trade time
    w = 1/4*(3*math.exp(-(0.1*x)**2) + 1/(0.1*x+1))
    return w
    

def predict(x): # tries to predict the next value of a series
    if isinstance(x, list):
        x = pd.Series(x).dropna()
        x_lst = x.tolist()
    absx = abs(x)   # we care about magnitude here
    x_lst = absx.dropna().tolist()
    weights = []
    normweights = []
    nweights = len(x_lst)
    weighted_ave_x = 0
    for i in range(len(x_lst)+1):
        coord = abs(i-len(x_lst))
        w = weight(coord)
        weights.append(w)  # appends weights from furthest to closest
    for i in range(nweights+1):
        normweight = weights[i]/sum(weights)
        normweights.append(normweight)
    for i in range(nweights):
        a = normweights[i]*x_lst[i]
        weighted_ave_x += a
    x_lst = x.dropna().tolist()
    #print(x_lst[-1])
    if x_lst[-1] > 0:    # if the last data point was positive, there is a pmcheck() chance of the next one being negative
        # if probability(pmcheck(x)):
        weighted_ave_x = -weighted_ave_x   # gives a percent chance of flipping the sign
        #return weighted_ave_x # MUST BE SAME INDENT AS IF STATEMENT OR ELSE IT WILL RETURN NONE
    elif x_lst[-1] < 0:
        # if probability(1-pmcheck(x)):  # if x_lst[-1] <0
            # weighted_ave_x = -weighted_ave_x
        return weighted_ave_x
    return weighted_ave_x # actually should just return price prediction? no I only want pred func to take in one arg

def pred_down(x, w, index): # x is data for desired derivative, w is the x' prediction
    if isinstance(x, list):
        x = pd.Series(x).dropna()
    derivatives = {}
    derivatives[0] = x
    #derivatives[1] = derivative(x)
    idx = 0
    while idx < index:
        idx+=1
        derivatives[idx] = derivative(derivatives[idx-1])
    for i in range(len(derivatives)):
        derivatives[i] = derivatives[i].dropna().tolist()
    derivatives[index].append(w)
    for i in range(index, 0, -1):
        #print(i)
        #print(derivatives[i-1][-1], derivatives[i][-1])
        derivatives[i-1].append(derivatives[i-1][-1] + derivatives[i][-1])
        #print (derivatives[i-1][-1])
    return derivatives[0][-1]

def pm_optimise(x): # finds the optimal derivative (highest output of pmcheck()) and returns that derivative
# note: should take in percentage_increase pd series
    probability = pmcheck(x)
    new_probability = pmcheck(derivative(x))
    index = 0
    derivatives = {}
    derivatives[0] = x
    while new_probability > probability:  # finds a local maxima
        index +=1
        derivatives[index] = derivative(derivatives[index-1])
        probability = pmcheck(derivatives[index-1])
        new_probability = pmcheck(derivatives[index])
    # while probability < 0.85:  # finds the derivative that meets a threshold value
    #     index +=1
    #     derivatives[index] = derivative(derivatives[index-1])
    #     probability = pmcheck(derivatives[index])
    # print(str(index)+"th derivative")
    y = derivatives[index]
    y = derivatives[index -1]  # for local minima while loop
    return y, index  # y is the first derivative that returns a pmcheck that is greater than the next derivative


# badly coded RMSE function
def RMSE(percentage_increase):
    percentage_increase_lst = percentage_increase.dropna().tolist()
    sumresidual = 0
    opt = pm_optimise(percentage_increase)
    idx = opt[1]
    iterations = 0
    # make a prediction at each percentage_increase data point at find the residual
    for i in range((len(percentage_increase)-1)):
        data = (percentage_increase[:-i-1]).dropna()
        if len(data) < 2*idx:   # checks if there is sufficient data left after slicing
            break
        iterations += 1
        optimised = pm_optimise(data)
        x = optimised[0]
        pred_x = predict(x)
        index = optimised[1]
        predicted_percentage_increase = pred_down(percentage_increase, pred_x, index)
        residual = predicted_percentage_increase - percentage_increase_lst[-i-1]
        residual_sq = residual**2
        sumresidual += residual_sq
    RMSE = math.sqrt(sumresidual/iterations)
    return RMSE
# NOTE: RMSE changes due to random nature of the magnitude for this model
# Ideally, the RMSE function would take in all historical data and make a prediction using the same amount of data as the main prediction
# this prediction is what the residuals should be calculated based on

def main(stock_name, data_period, resolution, shift):
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
    # percentage_acceleration = derivative(percentage_increase)
    # jerk = derivative(acceleration)
    # percentage_jerk = derivative(percentage_acceleration)
    # percentage_crackle = derivative(percentage_jerk)
    # percentage_pop = derivative(percentage_crackle)
    # percentage_sixth = derivative(percentage_pop)
    # percentage_seventh = derivative(percentage_sixth)
    optimised = pm_optimise(percentage_increase)
    x = optimised[0]
    pred_x = predict(x)
    index = optimised[1]
    error = RMSE(percentage_increase)
    predicted_percentage_increase = pred_down(percentage_increase, pred_x, index)
    print(stock_name)
    print ("The predicted percentage increase is " + str(round(predicted_percentage_increase, 3)) + "%")
    predicted_price = (predicted_percentage_increase/100+1)*latest_price
    pred_upper = predicted_price + (error/100)*latest_price
    pred_lower = predicted_price - (error/100)*latest_price
    print("The predicted price in", time_interval, "day(s) is", round(predicted_price, 3), "with an upper bound of", round(pred_upper, 3), "and a lower bound of", round(pred_lower, 3), "\n")


stock_name = input(f"Choose your stock: Format is the ticker name, e:g {AAPL} or {SnP_500}")
data_period = input(f"Choose your data_preiod --> e.g: {eight_days} for 8 days or even {two_months} for 2 months")                    
resolution = input(f"Choose your resolution: there are only these to choose from {default_res}")
time_interval = 1 # time interval from today in days (when do we want to hit the target price?)
shift = int(time_interval) # converts time interval into however many 15 min blocks. Note that there are 6.5 trading hours in a trading day
# formula for 1d resolution and for all integer time interval is int(time_interval)
# formula for 1h resolution and integer day time interval is int(time_interval*7)
# formula for 15m resolution and 1 day time interval is int(time_interval*6.5*4)
# formula for 15m resolution and 15m time interval (=1) is int(time_interval)
# formula for 1m resolution and 1 day time interval is int(time_interval*6.5*60)     
# formula for 1m resolution and 15 min time interval (1/(6.5*4)) is int(time_interval*6.5*60)

main(stock_name, data_period, resolution, shift)


# rough idea for clustering model
# make a model based on time-clustering of peaks of higher order derivative percentage changes 
        # need to somehow identify clusters, whether we are in a cluster and what the next move of the cluster will be
        # the absolute values might be useful here
        # maybe have some threshold value for absolute seventh order derivative and say that if abs is above that, its in a cluster, then spaces where it drops below threshold are between clusters?
        
# seventh_lst = percentage_seventh.dropna().tolist()   
# inc_lst = percentage_increase.dropna().tolist()
# accel_lst = percentage_acceleration.dropna().tolist()
# seventh_lst.append(predict(seventh_lst))
# plt.plot(range(len(seventh_lst)), seventh_lst)

# test_lst = pm_optimise(percentage_increase).dropna().tolist()
# test_lst.append(predict(test_lst))
# plt.plot(range(len(test_lst)), test_lst)



# preliminary predictions:
####### SPY #########
#    The predicted percentage increase is 1.249%
#    The predicted price in 1 day(s) is 417.967 with an upper bound of 430.524 and a lower bound of 405.41 
# made using 15m resolution, 6d data period

# The predicted percentage increase is 0.413%
# The predicted price in 15m is 414.514 with an upper bound of 418.355 and a lower bound of 410.673 
# made using 15m resolution, 6d data period
###### AAPL ##########
# The predicted percentage increase is 0.815%
# The predicted price in 1 day(s) is 174.969 with an upper bound of 186.853 and a lower bound of 163.085 
# made using 15m resolution, 6d data period

# The predicted percentage increase is 0.073%
# The predicted price in 15m is 173.682 with an upper bound of 181.841 and a lower bound of 165.523 
# made using 15m resolution, 6d data period

# check prediction during day time sg time on 12/5/2023



