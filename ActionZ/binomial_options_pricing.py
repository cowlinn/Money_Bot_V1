import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import pytz


# Initialise parameters
# symbol = "SPY"
# S0 = float(yf.Ticker(symbol).history(period = '1d', interval = '1m').iloc[-1]['Close'])      # initial stock price
# K = 450       # strike price
# T = 7/365         # time to maturity in years
# r = yf.Ticker("^TNX").history().iloc[-1]['Close'] / 100      # annual risk-free rate
# N = 3         # number of time steps
# u = 1.0104       # up-factor in binomial models
# d = 1/u       # ensure recombining tree
# opttype = 'C' # Option Type 'C' or 'P'

# copied from options.py directly
def find_option_contract(symbol, predicted_price, expiry_days, max_price, option_type):
    expiry_date = get_expiry_date(expiry_days)
    expiry_date_string = str(expiry_date).split()[0]
    try:
        option_chain = yf.Ticker(symbol).option_chain(expiry_date_string)
    except:
        print(f'No options expiring on {expiry_date_string} found for {symbol}! Try another date or a different ticker symbol!')
        return None
  
    # Filter option chain based on expiry date, option type, and maximum price
    options = option_chain.calls if option_type == 'call' else option_chain.puts
    
    # Filter out those that are above our max_price
    options = options[options['lastPrice'] <= max_price]

    # Find the closest match for the strike price
    options.reset_index(inplace=True)
    closest_strike = int(options['strike'].iloc[(options['strike'] - predicted_price).abs().idxmin()])

    options.index # not sure what this does
    # Filter options based on the closest strike price
    closest_option = options[options['strike'] == closest_strike]

    return closest_option


def american_slow_tree(K,T,S0,r,N,u,d,opttype='call'):
    #precompute values
    dt = T/N
    q = (np.exp(r*dt) - d)/(u-d)
    disc = np.exp(-r*dt)
    
    # initialise stock prices at maturity
    S = np.zeros(N+1)
    for j in range(0, N+1):
        S[j] = S0 * u**j * d**(N-j)
        
    # option payoff 
    C = np.zeros(N+1)
    for j in range(0, N+1):
        if opttype == 'P':
            C[j] = max(0, K - S[j])
        else:
            C[j] = max(0, S[j] - K)
    
    # backward recursion through the tree
    for i in np.arange(N-1,-1,-1):
        for j in range(0,i+1):
            S = S0 * u**j * d**(i-j)
            C[j] = disc * ( q*C[j+1] + (1-q)*C[j] )
            if opttype == 'put':
                C[j] = max(C[j], K - S)
            else:
                C[j] = max(C[j], S - K)
                
    return C[0]
# print(american_slow_tree(K,T,S0,r,N,u,d,opttype))

def american_fast_tree(K,T,S0,r,N,u,d,opttype='put'):
    #precompute values
    dt = T/N
    q = (np.exp(r*dt) - d)/(u-d)
    disc = np.exp(-r*dt)
    
    # initialise stock prices at maturity
    S = S0 * d**(np.arange(N,-1,-1)) * u**(np.arange(0,N+1,1))
        
    # option payoff 
    if opttype == 'put':
        C = np.maximum(0, K - S)
    else:
        C = np.maximum(0, S - K)
    
    # backward recursion through the tree
    for i in np.arange(N-1,-1,-1):
        S = S0 * d**(np.arange(i,-1,-1)) * u**(np.arange(0,i+1,1))
        C[:i+1] = disc * ( q*C[1:i+2] + (1-q)*C[0:i+1] )
        C = C[:-1]
        if opttype == 'put':
            C = np.maximum(C, K - S)
        else:
            C = np.maximum(C, S - K)
                
    return C[0]
# print(american_fast_tree(K,T,S0,r,N,u,d,opttype))

def test_upFactor(u, symbol="SPY", range_size = 50, option_type = 'call', silent = True, expiry_days = 7):
    if not silent:
        print(f'\nu is {u}')
    T = expiry_days/365         # time to maturity in years
    r = yf.Ticker("^TNX").history().iloc[-1]['Close'] / 100      # annual risk-free rate
    d = 1/u       # ensure recombining tree

    S0 = float(yf.Ticker(symbol).history(period = '1d', interval = '1m').iloc[-1]['Close'])      # initial stock price
    N = 3
    start_range = round(S0)-range_size
    end_range = round(S0) + range_size +1
    if range_size == 0:
        strike_price = round(S0)
        Option = find_option_contract(symbol, strike_price, expiry_days, 50, option_type)
        actual_price = Option['lastPrice'].iloc[0]
        our_price = american_fast_tree(strike_price, T, S0, r, N, u, d, option_type)
        diff = our_price-actual_price
        absdiff = abs(diff)
        if not silent:
            print(strike_price, actual_price, our_price, diff)
        return absdiff

    absdiff = 0
    iterations = 0
    for strike_price in range(start_range,end_range,5):
        Option = find_option_contract(symbol, strike_price, expiry_days, 50, option_type)
        if Option is None:
            continue
        actual_price = Option['lastPrice'].iloc[0]
        our_price = american_fast_tree(strike_price, T, S0, r, N, u, d, option_type)
        diff = our_price-actual_price
        absdiff += abs(diff)
        iterations += 1
        if not silent:
            print(strike_price, actual_price, our_price, diff)
    
    meandiff = absdiff/iterations
    if not silent:
        print(absdiff, meandiff)
    return absdiff, meandiff
    
# how good is it at pricing at the money options?
# optimal_u is some manually-calibrated best value of u
# this function is meant to improve your manual optimisation somewhat efficiently
def optimize_upFactor(u_start = 0.9, u_end = 1.1, symbol = "SPY", expiry_days = 7, optimal_u = 1.014, generation = 0, silent = True, option_type='call', fast = True, previous_middle = 0):
    if not silent:
        print(f'\nThis is generation {generation}')
    generation +=1
    if abs(u_start-u_end) < 0.0001:
        return u_start
    # range_start = int(u_start*1000)
    # range_end = int(u_end*1000)
    u_middle = (u_end+u_start)/2
    if u_middle == 1:
        u_middle+=0.0001
    middle_result = test_upFactor(u_middle, symbol, range_size=0, option_type=option_type, expiry_days=expiry_days)
    if middle_result > 1:
        u_middle = optimal_u
    if generation >= 3 and fast and previous_middle == u_middle:
        optimal_result = test_upFactor(optimal_u, symbol, range_size=0, option_type=option_type, expiry_days=expiry_days)
        if middle_result < optimal_result:
            return u_middle
        else:
            return optimal_u
    start_result = test_upFactor(u_start, symbol, range_size=0, option_type=option_type, expiry_days=expiry_days)
    end_result = test_upFactor(u_end, symbol, range_size=0, option_type=option_type, expiry_days=expiry_days)
    previous_middle = u_middle
    
    if not silent:
        print(f'middle is {u_middle}')
    if start_result < end_result and start_result < middle_result:
        return optimize_upFactor(u_start, u_middle, symbol, optimal_u = optimal_u, generation=generation, silent = silent, fast=fast, previous_middle=previous_middle, expiry_days=expiry_days)
    elif end_result < start_result and end_result < middle_result:
        return optimize_upFactor(u_middle, u_start, symbol, optimal_u = optimal_u, generation=generation, silent = silent, fast=fast, previous_middle=previous_middle, expiry_days=expiry_days)
    else:
        new_start = (u_middle+u_start)/2
        new_end = (u_middle+u_end)/2
        return optimize_upFactor(new_start, new_end, symbol, optimal_u = optimal_u, generation=generation, silent = silent, fast=fast, previous_middle=previous_middle, expiry_days=expiry_days)

def get_expiry_date(expiry_days):
    us_timezone = pytz.timezone('America/New_York')
    us_time =  datetime.now(us_timezone)
    days_to_add = expiry_days
    expiry_date = us_time + timedelta(days=days_to_add)
    return expiry_date

"""
# sanity check
symbol = 'SPY'
optimal_u = optimize_upFactor(symbol = symbol, option_type='put', expiry_days = 7)
wanted_strike = 458
S0 = float(yf.Ticker(symbol).history(period = '1d', interval = '1m').iloc[-1]['Close'])      # initial stock price
r = yf.Ticker("^TNX").history().iloc[-1]['Close'] / 100      # annual risk-free rate
N = 3
print(f'optimal up-factor is {optimal_u}')
print(f'actual price is {find_option_contract(symbol, wanted_strike, 7, 50, "put")["lastPrice"].iloc[0]}, our price is {american_fast_tree(wanted_strike,7/365,S0,r,N,optimal_u,1/optimal_u,"put")}')
"""