import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math

# statistical model
# Statistical model: consider all the price changes over a given historical period and give a probability distribution of the price movement (for example probability that price will move by a, prob that it will move by b, etc)
# idea 1: use normal distribution, defined by mu and sigma (since time frame is short and price changes are generally normally distributed for these time frames).
# from this distribution we can say what is the probability that price moves by a given amount\
# alternatively, we can also go by SD to give predictions, so 68% chance that price moves within one SD of the mean
# idea 2: use log normal distribution
# idea 3: weighted average to find prob dist?

# SIMPLE STATISTICAL MODEL
# this model only looks at historical price and uses stats to guess what the next price will be.
# it takes each historical price with equal weight and predicts what the next price at the next time interval will be.
# the model asks the question of "what is the likely price change given a time interval"
# this time interval will somewhat be dependent on the resolution variable
# it is likely to be highly in accurate


def f(x, sigma, mu): # normal distribution function
    return (1/(sigma*math.sqrt(2*math.pi)))*math.e**(-0.5*((x-mu)/sigma)**2)

def domain(x):
    rang = []
    for i in range(round(x.min())*100, round(x.max())*100):
        n = i/100
        rang.append(n)
    return rang

def shape_visual(x, name): # x is some variable, name is the name of that variable as a string
    plt.subplot(2,1,1)
    plt.hist(x, bins = 30)
    mean = str(round(x.mean(), 5))
    SD = str(round(x.std(), 5))
    name = name + ' histogram'
    plt.title(name)
    plt.subplot(2,1,2)
    plt.plot(domain(x), f(domain(x), x.std(), x.mean()))
    gauss_name = "gaussian distribution with mean " + mean + " and SD " + SD
    plt.title(gauss_name)
    plt.tight_layout(pad=1.0)
    plt.show()

def derivative(x):
    return x - x.shift()

def prob(x, lower, upper):  # integrate the probability distribution func to find probability
    #rang = domain(x)
    upper = int(upper * 1000)
    lower = int(lower * 1000)
    sigma = x.std()
    mu = x.mean()
    probability = 0
    for i in range(lower, upper):
        n = (i+1)/1000
        n_0 = i/1000
        dx = n - n_0
        I = f((n + n_0)/2, sigma, mu)
        probability += I*dx
    return (probability)

def boolprob(x, target_val):  # integrate the pdf from the left to ans the qn of what is the prob of getting something less than x
    rang = domain(x)
    target = int(target_val * 1000)
    sigma = x.std()
    mu = x.mean()
    probability = 0
    for i in range(int(rang[0]*1000), target):
        n = (i+1)/1000
        n_0 = i/1000
        dx = n - n_0
        I = f((n + n_0)/2, sigma, mu)
        probability += I*dx
    return (probability)

def dist(x): # returns two dicts with different key labelling (one is just for easy calling, the other is for ease of human comprehesion)
    price_dist = {}
    str_price_dist = {}
    rang = domain(x)
    for i in range(int(rang[0]*10), int(rang[-1]*10)):
        lower = i/10
        upper = (i+1)/10
        lower_to_upper = str(lower) + '% to ' + str(upper) + '%'
        str_price_dist[lower_to_upper] = prob(x, lower, upper)
        price_dist[lower] = prob(x, lower, upper)
    return price_dist, str_price_dist

def booldist(x):
    price_dist = {}
    str_price_dist = {}
    rang = domain(x)
    for i in range(int(rang[0]*10), int(rang[-1]*10)):
        target = i/10
        str_target = "probability of increase greater than " + str(target) + "%"
        str_price_dist[str_target] = 1 - boolprob(x, target)
        price_dist[target] = 1 - boolprob(x, target)
    return price_dist, str_price_dist

def main(stock_name, data_period, resolution, target_price, shift):
    # stock_name = "SPY"
    # data_period = "1y"
    # resolution = "1d"
    # target_price = 415  # in absolute price, can be a float
    # time_interval = 1 # time interval in days
    # shift = int(time_interval) # converts time interval into however many 15 min blocks. Note that there are 6.5 trading hours in a trading day
    # formula for 1d resolution and 1 day time interval is int(time_interval)
    # formula for 1h resolution and 1 day time interval is int(time_interval*6.5)
    # formula for 15m resolution and 1 day time interval is int(time_interval*6.5*4)
    # formula for 1m resolution and 1 day time interval is int(time_interval*6.5*60)
    ####################### CHANGE CONVERSION FORMULA IF CHANGING RESOLUTION ############################
    stock = yf.Ticker(stock_name)
    hist = stock.history(period = data_period, interval = resolution) # historical price data
    hist.reset_index(inplace=True) # converts datetime to a column
    hist['time_index'] = range(-len(hist.index), 0)
    hist['time_index'] += 1
    price = hist['Close']
    increase = price - price.shift(shift)
    percentage_increase = (increase/price.shift()*100).dropna()
    latest_price = hist['Close'][len(hist['Close'])-1]
    target_percentage_increase = (target_price - latest_price)/latest_price*100
    
    # NOTE: this will create shift number of NaN rows in increase series
    # bearing this is mind, the data_period must be greater than the time interval if we want to see significant predictions
    # each row in the increaase data is separated from its neighbouring row by the resolution
    # the increase data represents the gain/loss of a stock compared to 1 time interval ago
    hist['increase'] = increase
    increase = increase.dropna()
    # increase pd series object always has (shift) less rows than hist
    acceleration = derivative(increase)
    percentage_acceleration = derivative(percentage_increase)
    jerk = derivative(acceleration)
    acceleration_corrected_percentage_increase = percentage_increase + percentage_acceleration.mean()
    # crackle = derivative(jerk)
    # pop = derivative(crackle)
    
    
    # for the short time frames we are looking at, the distribution is generally symmetric
    # due to the 'momentum effect', we also should take direction into account
    
    
    shape_visual(increase, 'absolute price increase')
    shape_visual(percentage_increase, 'percentage price increase')
    shape_visual(acceleration_corrected_percentage_increase, 'acceleration-corrected percentage increase')
    shape_visual(acceleration, 'rate of change of interval-increases')
    shape_visual(percentage_acceleration, 'percentage acceleration')
    shape_visual(jerk, 'jerk')

    #shape_visual(crackle, 'crackle')
    #shape_visual(pop, 'pop')
    
    # devax the distribution looks horrendous
    
    # scaling the gaussian dist to fit the actual data
    #plt.hist(acceleration, bins = 30)
    #plt.plot(domain(acceleration), 70*f(domain(acceleration), acceleration.std(), acceleration.mean()))
    #plt.hist(jerk, bins = 30)
    #plt.plot(domain(jerk), 70*f(domain(jerk), jerk.std(), jerk.mean()))
    #plt.hist(jerk, bins = 30)
    
    ###################################### NOTES ########################################
    # absolute price increase over a 1 day period has really bad distribution until we look at 1 year time frame of historical data sampled
    # acceleration and jerk both have fairly good looking distributions across resolutions and time frames
    # mean of jerk and acceleraiton are usually very small (on the order of 1e-3 to 1e-4)
    # they also have relatively small SD on the order of 1e-1
    #
    # in the 1 min resolution, if expectation of jerk is ~ 0 with small SD, we can say a_n ~ a_(n+1) and v_n+1 ~ 2(v_n) - v_(n-1)
    # this 1 min model, however, is not that useful as what it predicts is the change in the next minute
    # a possible usecase for this method might be making a real time trading bot that constantly tries to predict the next price movement
    # from here, we can make trades based on the forecasted price in the next minute (or maybe 15 minutes)
    # this is implemented in statistical acceleration model
    #
    # we can expand this model to lower resolutions that enable longer term predictions using error prop?
    # I found that percentage price increase actually has a lower SD and percentage error so I will use that and convert this into absolute price for options usage
    #####################################################################################
    if target_percentage_increase >= 0:
        target_prob = 1-boolprob(acceleration_corrected_percentage_increase, target_percentage_increase)
    else:
        target_prob = boolprob(acceleration_corrected_percentage_increase, target_percentage_increase)
    expected_price = ((acceleration_corrected_percentage_increase.mean())/100+1)*latest_price
    upper_bound = expected_price + ((acceleration_corrected_percentage_increase.std())/100)*latest_price
    lower_bound = expected_price - ((acceleration_corrected_percentage_increase.std())/100)*latest_price
    # there is a 68% chance price falls within upper and lower bound
    print("Probability of reaching target price of", target_price, "for", stock_name, "by the end of", time_interval, "day(s) is", round(target_prob, 3))
    print("The expected price is", round(expected_price, 3), "with upper bound of", round(upper_bound, 3), "and lower bound of", round(lower_bound, 3))
    return
stock_name = "SPY"
data_period = "1y"
resolution = "1d"
target_price = 411  # in absolute price, can be a float. target price will most likely be the option strike price.
time_interval = 1 # time interval from today in days (when do we want to hit the target price?)
shift = int(time_interval) # converts time interval into however many 15 min blocks. Note that there are 6.5 trading hours in a trading day
# formula for 1d resolution and for all integer time interval is int(time_interval)
# formula for 1h resolution and 1 day time interval is int(time_interval*6.5)
# formula for 15m resolution and 1 day time interval is int(time_interval*6.5*4)
# formula for 1m resolution and 1 day time interval is int(time_interval*6.5*60)
main(stock_name, data_period, resolution, target_price, shift)



# preliminary predictions to check on 9/5/2023
# Probability of reaching target price of 415 for SPY by the end of 1 day(s) is 0.371
# The expected price is 413.095 with upper bound of 418.79 and lower bound of 407.399

# Probability of reaching target price of 411 for SPY by the end of 1 day(s) is 0.37
# The expected price is 412.858 with upper bound of 418.55 and lower bound of 407.166

# Probability of reaching target price of 312 for MSFT by the end of 1 day(s) is 0.438
# The expected price is 310.953 with upper bound of 317.597 and lower bound of 304.309

# Probability of reaching target price of 309 for MSFT by the end of 1 day(s) is 0.384
# The expected price is 310.953 with upper bound of 317.597 and lower bound of 304.309

# Probability of reaching target price of 174 for AAPL by the end of 1 day(s) is 0.473
# The expected price is 173.736 with upper bound of 177.395 and lower bound of 170.076

# Probability of reaching target price of 175 for AAPL by the end of 1 day(s) is 0.367
# The expected price is 173.736 with upper bound of 177.395 and lower bound of 170.076