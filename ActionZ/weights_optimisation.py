import numpy as np
import pandas as pd
import ta_lib
import talib
import yfinance as yf
import os
import csv

"""
how to call:
    optimise(data, interval=0.1, min_sample_size=5, stock_name = 'SPY') # gives an optimised ordered list of weights
or: 
    backtest(data, optimise(data, interval=0.1, min_sample_size=5, stock_name = 'SPY'), 'SPY')

for rael bot:
    just take the optimised weights, copy the code in backtest and just take the latest readings to output some trade action (repplace the buy/sell prints)

Some Results:
- the usefulness of each indicator varies wildly??
- we cannot just optimise for winrate - if the losses are much larger than the wins, we will still loose money
- we may need one more optimisation function?
- two single optimised results (backtest(data, 0.125, 0, 0.125, 0.5, 0.125)) and backtest(data, 0.1, 0.1, 0.4, 0.3, 0.1))
  gave identical winrates but very different gains, for the same number of trades over 10 days
- using 30 days of 15m data, backtest(data, 0.1, 0.3, 0.3, 0, 0.3) gives an insane result of (74.36, 56.2188720703125, 39)
  74% winrate over 39 trades plus a HUGE gain??
"""


def forex(stock_name):
    return stock_name.upper()[-2:] == '=X'

# stock_name = "AMZN"
data_period = "3d" # set this to about 2-3 days for using weights_file_reader()
resolution = "15m"
# stock = yf.Ticker(stock_name)  # this goes in main()
# data = stock.history(period = data_period, interval = resolution) # historical price data
def menal(Nweights):
    baasly = []
    for i in range(1, Nweights+1):
        entry = (0.0, i)
        baasly.append(entry)
    return baasly

# function to make bactesting directly from weights files easier (AAR)
# to use, just dump all the weights files into a test_data folder and run
def weights_file_reader():
    current_stocks_to_monitor =  ['SPY', 'TSLA', 'NVDA', 'V', 'MA', 'AMD', 'PYPL', 'GME', 'PLTR', 
                                    'MSFT', 'GOOGL', 'JPM', 'DIS', 'NFLX', 'MMM', 'CAT', 'NKE', 
                                    'WMT','COST', 'CSCO', 'PFE', 'SSL', 'RIOT', 'GILD', 'AMZN', 'BABA',
                                    'META', 'FSLR', 'ORCL', 'PEP', 'MCD', 'ABT', 'SBUX']
    parent_dir = 'test_data/'
    backtest_results = {}
    for stock_name in current_stocks_to_monitor:
        fullpath = os.path.join(parent_dir, f"{stock_name}_optimised-weights.txt")
        if not os.path.exists(fullpath):
            print(f'No weights file for {stock_name}')
            print(fullpath)
            continue
        weights_file = open(fullpath, "r")
        optimised_weights = []
        optimised_weights_data = csv.reader(weights_file, delimiter='\n')
        for row in optimised_weights_data:
            optimised_weights.append(float(row[0]))
        weights_file.close()
        stock = yf.Ticker(stock_name)  # this goes in main()
        data = stock.history(period = data_period, interval = resolution) # historical price data 
        print(f"Now backtesting {stock_name}")
        backtest_results[stock_name] = backtest(data, optimised_weights, stock_name)
    return backtest_results

def backtest(data, ordered_weights, stock_name, threshold = 0.4): # ordered_weights is a list of weights in the same order as the output of ta_lib.TA()
    Nweights = len(ta_lib.TA(data, forex(stock_name)).iloc[0]) # number of weights required according to ta_lib.py (basically how many indactors we are using)
    if len(ordered_weights) != Nweights: # check if the input weights are valid
        # print('Incorrect number of weights!')
        return
    data = data.copy()
    data.reset_index(inplace=True) # converts datetime to a column
    data['ATR'] = talib.ATR(data['High'], data['Low'], data['Close'])
    calls = {}
    puts = {}
    total_trades = 0
    wins = 0
    losses = 0
    gains = 0
    for i in range(40, len(data)):
        current_data = data.iloc[i]
        # current_hour = int(str(current_data['Datetime']).split()[1][0:2])
        # current_minute = int(str(current_data['Datetime']).split()[1][3:5])
        current = ta_lib.TA(data.loc[:i], forex(stock_name))
        output = 0
        for i in range(Nweights):
            output += ordered_weights[i]*current.iloc[0][i] # apply the weights
        # if current_hour > 13: # do not enter trades after 2pm
        #     # print(current_data['Datetime'])
        #     continue
        # opening positions
        if output >= threshold:
            # print ('Buy a call at '+str(current_data['Datetime']))
            stoploss = current_data['Close']-current_data['ATR']*1.5  #1.5 # set tighter stoploss/takeprofit
            takeprofit = current_data['Close']+current_data['ATR']*1.875  #1.875
            try:
                calls[str(current_data['Datetime'])] = (current_data['Close'], stoploss, takeprofit)
            except:
                calls[str(current_data['Date'])] = (current_data['Close'], stoploss, takeprofit)
            total_trades += 1
        elif output <= -threshold:
            # print('Buy a put at '+str(current_data['Datetime']))
            stoploss = current_data['Close']+current_data['ATR']*1.5
            takeprofit = current_data['Close']-current_data['ATR']*1.875
            try:
                puts[str(current_data['Datetime'])] = (current_data['Close'], stoploss, takeprofit)
            except:
                puts[str(current_data['Date'])] = (current_data['Close'], stoploss, takeprofit)
            total_trades += 1
        
        # closing positions
        remove = []
        for i in calls:
            trade_info = calls[i]
            if current_data['Close'] < trade_info[1]:
                # stoploss triggered, close the position
                losses += 1
                gains += current_data['Close']-trade_info[0] # count the profit/loss
                # print('It is currently ' + str(current_data['Datetime']) + '. Sell the call purchased at ' + i)
                # print(trade_info[0]-current_data['Close'] ,'baaasly trade')
                remove.append(i)
            elif current_data['Close'] > trade_info[2]:
                # takeprofit reached, close the position
                wins += 1
                gains += current_data['Close']-trade_info[0] # count the profit/loss
                # print('It is currently ' + str(current_data['Datetime']) + '. Sell the call purchased at ' + i)
                # print(current_data['Close']-trade_info[0],'guuuud trade')
                remove.append(i)
        for i in remove:
                # remove closed positions from dictionary of open positions
                calls.pop(i)
        
        remove = []
        for i in puts:
            trade_info = puts[i]
            if current_data['Close'] < trade_info[2]:
                # takeprofit reached, close the position
                wins += 1
                gains += trade_info[0]-current_data['Close'] # count the profit/loss
                # print('It is currently ' + str(current_data['Datetime']) + '. Sell the put purchased at ' + i)
                # print(trade_info[0]-current_data['Close'] ,'guuuud trade')
                remove.append(i)
            elif current_data['Close'] > trade_info[1]:
                # stoploss triggered, close the position
                losses += 1
                gains += trade_info[0]-current_data['Close'] # count the profit/loss
                # print('It is currently ' + str(current_data['Datetime']) + '. Sell the put purchased at ' + i)
                # print(trade_info[0]-current_data['Close'] ,'baaasly trade')
                remove.append(i)
        for i in remove:
                # remove closed positions from dictionary of open positions
                puts.pop(i)
    completed_trades = wins + losses
    # if completed_trades == total_trades:
        # print('All', completed_trades, 'trades completed')
    if wins == 0:
        winrate = 0 # actually the trueWinrate for the case where no trades are made is 50%, for something like 0 wins 5 losses, the trueWinrate is 14%
        # but we don't want any of these shitty strategies anyway so to ensure there is no chance it is included, we just return 0
        return winrate, gains, completed_trades
    winrate = round(wins/completed_trades*100, 3)
    trueWinrate = round((wins+1)/(completed_trades+2), 3) # differentiates between something like 3/5 and 60/100 (both have winrate of 60% but 3/5 has trueWinrate of 57.1% while 50/100 has trueWinrate of 59.8%)
    return trueWinrate, gains, completed_trades #, calls, puts

def initial_optimise(data, interval, stock_name, min_sample_size = 15, threshold = 0.4):
    test_log = {}
    iterr = range(0,int(1/interval))
    Nweights = len(ta_lib.TA(data, forex(stock_name)).iloc[0]) # number of weights required according to ta_lib.py (basically how many indactors we are using)
    for i in iterr:
        for k in range(1, 1+Nweights):
            test_weight = i*interval
            name = str(test_weight) + ' ' + str(k)
            result = backtest(data, interpret([(test_weight, k)], data, stock_name), stock_name, threshold = threshold)
            if result[2] >= min_sample_size and result[1] > 0: # only consider results with a min sample size and actual profit
                test_log[name] = result[0]
    if test_log:
        best_weight = max(test_log, key = test_log.get)
        result = best_weight.split()
        result[0] = float(result[0])
        result[1] = int(result[1])
        return [tuple(result)]
    elif min_sample_size == 0:
        return [(0.0, 1)]
    else:
        # no suitable optimisations found. not a good idea to trade.
        min_sample_size -= 1
        return initial_optimise(data, interval, stock_name, min_sample_size, threshold = threshold) # reduce sample size requirement until some prediction is made?

def second_optimise(data, interval, initial_results, stock_name, min_sample_size = 15, threshold = 0.4):
    fixed_weight_number_lst = []
    fixed_weight_dict = {}
    for i in range(len(initial_results)):
        fixed_weight_number_lst.append(initial_results[i][1]) # which weights have been fixed?
        fixed_weight_dict[initial_results[i][1]] = initial_results[i][0]
    test_log = {}
    total_fixed_weight = sum(fixed_weight_dict.values())
    iterr = range(0,int((1-total_fixed_weight)/interval)+1)
    Nweights = len(ta_lib.TA(data, forex(stock_name)).iloc[0]) # number of weights required according to ta_lib.py (basically how many indactors we are using)
    for k in range(1, 1+Nweights):
        if (k in fixed_weight_number_lst):
            continue
        for i in iterr:
            test_weight = i*interval
            name = str(test_weight) + ' ' + str(k)
            copy = initial_results.copy()
            copy.append((test_weight, k))
            input_weights = interpret(copy, data, stock_name)
            result = backtest(data, input_weights, stock_name, threshold = threshold)
            if result[2] >= min_sample_size and result[1] > 0:
                test_log[name] = result[0]
    if test_log:
        best_weight = max(test_log, key = test_log.get)
        # print(test_log[best_weight])
        second_lst = best_weight.split()
        second_lst[0] = float(second_lst[0])
        second_lst[1] = int(second_lst[1])
        final = initial_results.copy()
        final.append(tuple(second_lst)) # this changes the original result too (can use a shallow copy if this is not desired)
        return final, test_log[best_weight]
    elif min_sample_size == 0: # if got no good options, dun anyhow trade
        devax = menal(Nweights) # just set all the weights to 0 to guarantee no trading occurs
        return devax, 0
    else:
        # no suitable optimisations found. not a good idea to trade.
        min_sample_size -= 1
        return second_optimise(data, interval, initial_results, stock_name, min_sample_size, threshold = threshold) # reduce sample size requirement until some prediction is made?

def optimise(data, interval, min_sample_size, stock_name, threshold = 0.4):
    Nweights = len(ta_lib.TA(data, forex(stock_name)).iloc[0]) # number of weights required according to ta_lib.py (basically how many indactors we are using)
    initial = initial_optimise(data, interval, stock_name, min_sample_size, threshold = threshold)
    second= second_optimise(data, interval, initial, stock_name, min_sample_size, threshold = threshold)
    optimised_weights = second[0]
    backtested_winrate = second[1]

    while len(optimised_weights) < Nweights-1:
        second = second_optimise(data, interval, optimised_weights, stock_name, min_sample_size, threshold = threshold)
        backtested_winrate = second[1]
        optimised_weights = second[0]
    ordered_weights = interpret(optimised_weights, data, stock_name)
    print('Backtested winrate:\n', str(backtested_winrate*100)+'%')
    print('Ordered weights:\n', ordered_weights, '\n')
    return ordered_weights
 
def interpret(optimised_output, data, stock_name):
    Nweights = len(ta_lib.TA(data, forex(stock_name)).iloc[0]) # number of weights required according to ta_lib.py (basically how many indactors we are using)
    if optimised_output == menal(Nweights):
        baasly = list(np.zeros(Nweights))
        return baasly
    fixed_weight = 0
    Nfixed = len(optimised_output)
    fixed_weight_lst = []
    fixed_weight_dict = {}
    for i in range(len(optimised_output)):
        fixed_weight += optimised_output[i][0]
        fixed_weight_lst.append(optimised_output[i][1])
        fixed_weight_dict[optimised_output[i][1]] = optimised_output[i][0]
    normalised_weight = (1-fixed_weight)/(Nweights-Nfixed)
    dic = {}
    for i in range(1,Nweights+1):
        if (i in fixed_weight_lst):
            dic[i] = fixed_weight_dict[i]
        else:
            dic[i] = normalised_weight
    ordered_weights = []
    for i in dic:
        ordered_weights.append(dic[i])
    return ordered_weights