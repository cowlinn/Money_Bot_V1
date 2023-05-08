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

stock_name = "SPY"
data_period = "5d"
resolution = "15m"