import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.signal import butter, lfilter, freqz
from scipy.fft import rfft, rfftfreq, irfft, fft, ifft, fftfreq
import math

# statistical model
# Statistical model: consider all the price changes over a given historical period and give a probability distribution of the price movement (for example probability that price will move by a, prob that it will move by b, etc)
# idea 1: use normal distribution, defined by mu and sigma (since time frame is short and price changes are generally normally distributed for these time frames).
# from this distribution we can say what is the probability that price moves by a given amount\
# alternatively, we can also go by SD to give predictions, so 68% chance that price moves within one SD of the mean
# idea 2: use log normal distribution
# idea 3: weighted average to find prob dist?

# STATISTICAL ACCELERATION MODEL
# This model first checks if jerk is small, and only proceeds if it is near 0 with small enough SD
# with this condition fulfilled, we can say a_n ~ a_(n+1) and v_n+1 ~ 2(v_n) - v_(n-1)
# this allows us to predict price movment in the next small timeframe
# a possible usecase for this method might be making a real time trading bot that constantly tries to predict the next price movement
# from here, we can make trades based on the forecasted price in the next minute (or maybe 15 minutes)
# It is likely that this model will only work for very high resolution graphs (1m to 15m)
# note: Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo]

stock_name = "SPY"
data_period = "5d"
resolution = "1m"
stock = yf.Ticker(stock_name)
hist = stock.history(period = data_period, interval = resolution) # historical price data
