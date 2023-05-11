import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math

# STATISTICAL ACCELERATION MODEL
# This model first checks if jerk is small, and only proceeds if it is near 0 with small enough SD
# with this condition fulfilled, we can say a_n ~ a_(n+1) and v_n+1 ~ 2(v_n) - v_(n-1)
# this allows us to predict price movment in the next small timeframe
# a possible usecase for this method might be making a real time trading bot that constantly tries to predict the next price movement
# from here, we can make trades based on the forecasted price in the next minute (or maybe 15 minutes)
# It is likely that this model will only work for very high resolution graphs (1m to 15m)
# note: Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]
# one limitation is that this probably will not work well for the opening 30 min of the trading day which usually has really high volatility

def derivative(x):
    return x - x.shift()

def predict(percentage_increase):
    if isinstance(percentage_increase, list):
        #percentage_increase_lst = percentage_increase
        percentage_increase = pd.Series(percentage_increase)
        percentage_increase_lst = percentage_increase.tolist()
    percentage_increase_lst = percentage_increase.tolist()
    percentage_acceleration = derivative(percentage_increase)
    percentage_acceleration_lst = percentage_acceleration.tolist()
    #percentage_increase = percentage_increase.tolist()
    #for i in range(100): # predict the next 100 15min changes 
    #    latest_percentage_increase = percentage_increase[-1]
    #    previous_percentage_increase = percentage_increase[-2]
    #    next_percentage_increase = 2*latest_percentage_increase - previous_percentage_increase
    #    print(next_percentage_increase)
    #    percentage_increase.append(next_percentage_increase)
    #
    # quite baasly to make extremely extrapolated predictions (it just says price keeps going up or down)
    # this is because in the long run, acceleration is not actually a constant
    # need to keep updating percentage_increase with real data
    
    # I should factor in the average local acceleration for the momentum effect
    
    # weighted average acceleration to be added to velocity
    weights = []
    normweights = []
    nweights = 10   # number of weights
    for i in range(1,nweights+1):
        weight = 1/i
        weights.append(weight)
    for i in range(nweights):
        normweight = weights[i]/sum(weights)
        normweights.append(normweight)
    weighted_ave_acceleration = 0
    for i in range(nweights):
        a = normweights[i]*percentage_acceleration_lst[-1-i]
        weighted_ave_acceleration += a
    #print(weighted_ave_acceleration, "test")
    # aparently adding the weighted acceleration sometimes increases RMSE
    
    latest_percentage_increase = percentage_increase_lst[-1]
    previous_percentage_increase = percentage_increase_lst[-2]
    next_percentage_increase = 2*latest_percentage_increase - previous_percentage_increase
    acceleration_next_percentage_increase = next_percentage_increase + weighted_ave_acceleration
    # next percentage increase is our predicted outcome

    return next_percentage_increase, acceleration_next_percentage_increase, nweights

# badly coded RMSE function
def RMSE(percentage_increase):
    percentage_increase_lst = percentage_increase.tolist()
    sumresidual = 0
    asumresidual = 0
    nweights = predict(percentage_increase)[2]
    # make a prediction at each percentage_increase data point at find the residual
    for i in range(nweights, len(percentage_increase)-1):
        predVnp1 = predict(percentage_increase[:i+1])[0]
        Vnp1 = percentage_increase_lst[i+1]
        residual = predVnp1 - Vnp1
        residual_sq = residual**2
        sumresidual += residual_sq
    RMSE = math.sqrt(sumresidual/(len(percentage_increase)-2))
    for i in range(nweights, len(percentage_increase)-1):
        predVnp1 = predict(percentage_increase[:i+1])[0]
        Vnp1 = percentage_increase_lst[i+1]
        residual = predVnp1 - Vnp1
        residual_sq = residual**2
        asumresidual += residual_sq
    aRMSE = math.sqrt(asumresidual/(len(percentage_increase)-2))
    return RMSE, aRMSE
# Ideally, the RMSE function would take in all historical data and make a prediction using the same amount of data as the main prediction
# this prediction is what the residuals should be calculated based on

def main(stock_name, data_period, resolution, shift):
    stock = yf.Ticker(stock_name)
    hist = stock.history(period = data_period, interval = resolution) # historical price data
    hist.reset_index(inplace=True) # converts datetime to a column
    hist['time_index'] = range(-len(hist.index), 0)
    hist['time_index'] += 1
    price = hist['Close']
    latest_price = hist['Close'][len(hist['Close'])-1]
    increase = price - price.shift(shift)
    percentage_increase = (increase/price.shift()*100).dropna()
    hist['increase'] = increase
    increase = increase.dropna()
    percentage_acceleration = derivative(percentage_increase)
    percentage_jerk = derivative(percentage_acceleration)
    jerk_mean = percentage_jerk.mean()
    jerk_SD = percentage_jerk.std()
    if jerk_mean<1e-4 and jerk_SD<0.1:
        prediction = predict(percentage_increase)
        predicted_price = (prediction[0]/100+1)*latest_price
        a_predicted_price = (prediction[1]/100+1)*latest_price
        error = RMSE(percentage_increase)
        pred_upper = predicted_price + (error[0]/100)*latest_price
        pred_lower = predicted_price - (error[0]/100)*latest_price
        a_pred_upper = a_predicted_price + (error[1]/100)*latest_price
        a_pred_lower = a_predicted_price - (error[1]/100)*latest_price
        print(error)
        print("Without taking acceleration into account, the predicted price in", shift, "min is", round(predicted_price, 3), "with an upper bound of", round(pred_upper, 3), "and a lower bound of", round(pred_lower, 3), "\n")
        print("Taking acceleration into account, the predicted price in", shift, "min is", round(a_predicted_price, 3), "with an upper bound of", round(a_pred_upper, 3), "and a lower bound of", round(a_pred_lower, 3))
    else:
        print("\n##################### WARNING: jerk is large and this model will be inaccurate! #####################\n")
        prediction = predict(percentage_increase)
        predicted_price = (prediction[0]/100+1)*latest_price
        a_predicted_price = (prediction[1]/100+1)*latest_price
        error = RMSE(percentage_increase)
        pred_upper = predicted_price + (error[0]/100)*latest_price
        pred_lower = predicted_price - (error[0]/100)*latest_price
        a_pred_upper = a_predicted_price + (error[1]/100)*latest_price
        a_pred_lower = a_predicted_price - (error[1]/100)*latest_price
        print(error)
        print("Without taking acceleration into account, the predicted price in", shift, "min is", round(predicted_price, 3), "with an upper bound of", round(pred_upper, 3), "and a lower bound of", round(pred_lower, 3), "\n")
        print("Taking acceleration into account, the predicted price in", shift, "min is", round(a_predicted_price, 3), "with an upper bound of", round(a_pred_upper, 3), "and a lower bound of", round(a_pred_lower, 3))

    return
stock_name = "SPY"
data_period = "5d"
resolution = "1m"
time_interval = 1/(6.5*4) # we want to know what the price in 15min wil be
shift = int(time_interval*6.5*60) # converts time interval into however many 15 min blocks. Note that there are 6.5 trading hours in a trading day
# formula for 1d resolution and for all integer time interval is int(time_interval)
# formula for 1h resolution and 1 day time interval is int(time_interval*7)
# formula for 15m resolution and 1 day time interval is int(time_interval*6.5*4)
# formula for 2m resolution and 1 day time interval is int(time_interval*6.5*30)
# formula for 1m resolution and 1 day time interval is int(time_interval*6.5*60)
# formula for 1m resolution and 15 min time interval (1/(6.5*4)) is int(time_interval*6.5*60)

main(stock_name, data_period, resolution, shift)

# increase pd series object always has (shift) less rows than hist


############################################ NOTES ############################################
# this relatively simple model only looks at the most recent 2 data points to predict the next one
# I also tried factoring in the acceleration by looking at the last nweight acceleration values and taking their weighted average, biased towards recent acceleration
# the only thing taking in historical data is RMSE and the last nweight coordinates of acceleration
# increasing the data period is likely to increase RMSE as it just gives more points of comparison for RMSE
# that being said, it is not a good idea to attempt to simply minimise RMSE as this is probably overfitting
# ultimately we want a reasonable margin of error to make good trading decisions so RMSE is not everything
###############################################################################################

### check predictions for SPY on 12/5/2023
# Without taking acceleration into account, the predicted price in 15 min is 412.32 with an upper bound of 412.665 and a lower bound of 411.975 

# Taking acceleration into account, the predicted price in 15 min is 412.354 with an upper bound of 412.699 and a lower bound of 412.009




