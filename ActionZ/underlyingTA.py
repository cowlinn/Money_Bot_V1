import pandas as pd
import ta_lib
import talib
import yfinance as yf
import weights_optimisation
import sys
import os 
import csv
import datetime

"""
how to call:
    - by importing:
        
        import underlyingTA
        stock_name = 'SPY'
        trades = underlyingTA.decision(stock_name)
        
        or
        
        stock_lst = ['SPY', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'GOOGL', 'NVDA', 'MA', 'V']
        for i in stock_lst:
            underlyingTA.optimise_decision(i) # it will just write a bunch of log files
            

    - by running from bash script or command line or something?
        idk what we are gonna use so the example below is some code for a bash script (btw I can't rmb if bash will parse arguments as strings by default?)
        
        for ticker in SPY AAPL TSLA MSFT AMZN GOOGL NVDA MA V;
            do ./underlyingTA.py $ticker 4d 15m;
        done
    
        ok I did some googling and tried it out, for powershell its:
        
        python underlyingTA.py SPY 4d 15m
        
        in place of the ./underlyingTA.py $ticker 4d 15m
        
        # if we don't want to call it in this way just comment off the if statements at the bottom
        
        
# note: if you do the list of tickers thing, it will take a long ass time because it does it sequentially.
        Should probably split it into multiple loops.
"""
# make a trading decision based on current available market information
def optimise_decision(stock_name, data_period = '4d', resolution = '15m'):
    calls = {}
    puts = {}

    # call the data
    stock = yf.Ticker(stock_name)  # this goes in main()
    data = stock.history(period = data_period, interval = resolution) # historical price data
    data.reset_index(inplace=True) # converts datetime to a column
    data['ATR'] = talib.ATR(data['High'], data['Low'], data['Close'])
    current_data = data.iloc[-1] 
    current_date = str(data['Datetime'].iloc[-1]).split()[0]
    min_samples = int(data_period[:-1]) # average of 1 trade per day?
    optimisation_interval = 0.01
    if weights_optimisation.forex(stock_name):
        optimisation_interval = 0.05
    # get optimised weights by backtesting through the data_period. Weights have precision of 0.1
    # changed the precision to 0.01 (it takes about 3 min and 20s to run as compared to 20s for 0.1)
    # at 15m resolution the 3min is not THAT bad considering we only run this like once or twice a day?
    optimised_weights = weights_optimisation.optimise(data, interval = optimisation_interval, min_sample_size = min_samples, stock_name = stock_name)
   
    # write optimised weigths to a file
    parent_dir = 'Optimised-weights/'
    weights_file_name = current_date + '_' + stock_name +'_optimised-weights.txt'
    fullpath = os.path.join(parent_dir, weights_file_name)
    if not os.path.exists(parent_dir):
        os.mkdir(parent_dir)
    weights_file = open(fullpath, "w") # "w" because we only want ONE set of weights at a time for a given ticker on a given trading day
    # assume we want to keep logs of the weights for each day for now, if we dun need can just remove current-date from the filename
    for i in optimised_weights:
        weights_file.write(str(i)+'\n')
    weights_file.close()
    
    backtest_results = weights_optimisation.backtest(data, optimised_weights, stock_name)
    if backtest_results[0] < 50:
        return ({}, {}) # do nothing if the current strategy is unlikely to work (has winrate < 50%)
    
    # get current trading signal using the weights
    unweighted_signals = ta_lib.TA(data, weights_optimisation.forex(stock_name))
    Nweights = len(unweighted_signals.iloc[0]) # number of weights required according to ta_lib.py (basically how many indactors we are using)
    overall_signal = 0
    for i in range(Nweights):
        overall_signal += optimised_weights[i]*unweighted_signals.iloc[0][i] # apply the weights

    # make the decisions based on the same thresholds used in weights_optimisation.py
    if overall_signal > 0.4:
        # price predicted to go up
        # print ('Buy a call at '+str(current_data['Datetime']))
        stoploss = current_data['Close']-current_data['ATR']*2
        takeprofit = current_data['Close']+current_data['ATR']*2.5
        """
        Execute trade here? app.buy(call)
        Or we can just have the optionsTA.py file read the suggested trade actions in the log file and see if got any good options?
        """
        # write trade actions to a file
        parent_dire = 'Trade-action-logs/'
        filename = current_date + '_' + stock_name +'_call-logs.txt'
        fullpath = os.path.join(parent_dire, filename)

        if not os.path.exists(parent_dire):
            os.mkdir(parent_dire)
            
        call_file = open(fullpath, "a+")
        # data is written in the format of transaction timestamp, underlying price at time of purchase, stoploss, takeprofit
        call_file.write(str(current_data['Datetime']) + '\t' + str(current_data['Close']) + '\t' + str(stoploss) + '\t' + str(takeprofit) + '\n')
        call_file.close()
        calls[str(current_data['Datetime'])] = (current_data['Close'], stoploss, takeprofit)

        
    elif overall_signal < -0.4:
        # print('Buy a put at '+str(current_data['Datetime']))
        stoploss = current_data['Close']+current_data['ATR']*2
        takeprofit = current_data['Close']-current_data['ATR']*2.5
        """
        Execute trade here? app.buy(put)
        Or we can just have the optionsTA.py file read the suggested trade actions in the log file and see if got any good options?
        """
        # write trade actions to a file
        parent_dire = 'Trade-action-logs/'
        filename = current_date + '_' + stock_name +'_put-logs.txt'
        fullpath = os.path.join(parent_dire, filename)

        if not os.path.exists(parent_dire):
            os.mkdir(parent_dire)

        put_file = open(fullpath, "a+")
        # data is written in the format of transaction timestamp, underlying price at time of purchase, stoploss, takeprofit
        put_file.write(str(current_data['Datetime']) + '\t' + str(current_data['Close']) + '\t' + str(stoploss) + '\t' + str(takeprofit) + '\n')
        put_file.close()
        puts[str(current_data['Datetime'])] = (current_data['Close'], stoploss, takeprofit)

        """"
        Assume that the stoploss/take profit is set in the broker and it will auto close the position if either one is hit
        """
    print('DONE!!')
    return calls,puts # in case we want to just call this script directly from another python script

# make a trading decision based on current available market information
def decision(stock_name, data_period = '4d', resolution = '15m'):
    calls = {}
    puts = {}
    if weights_optimisation.forex(stock_name):
        print('Currently performing TA for forex pair '+ stock_name[:-2]+'.')
    else:
        print('Currently performing TA for '+ stock_name+'.')
    # call the data
    stock = yf.Ticker(stock_name)  # this goes in main()
    data = stock.history(period = data_period, interval = resolution) # historical price data
    data.reset_index(inplace=True) # converts datetime to a column
    data['ATR'] = talib.ATR(data['High'], data['Low'], data['Close'])
    current_data = data.iloc[-1] 
    current_date = str(data['Datetime'].iloc[-1]).split()[0]
    
    # get optimised weights by reading from file
    parent_dir = 'Optimised-weights/'
    weights_file_name = current_date + '_' + stock_name +'_optimised-weights.txt'
    fullpath = os.path.join(parent_dir, weights_file_name)
    if not os.path.exists(fullpath): # if u call this as the first decision of the day
        print('Performing first optimisation of the day.')
        return optimise_decision(stock_name, data_period, resolution)
    weights_file = open(fullpath, "r")
    optimised_weights = []
    optimised_weights_data = csv.reader(weights_file, delimiter='\n')
    for row in optimised_weights_data:
        optimised_weights.append(float(row[0]))
    weights_file.close()
    
    baasly = 0
    if sum(optimised_weights) == baasly: # if the previous optimisation was baasly (no samples with good success rate)
        print('Previous optimisation unsuccessful, retrying optimsation!')
        return optimise_decision(stock_name, data_period, resolution) # run the optimsation again and return the (potentially) new result instead. Also, rewrite the weights file if it is different
    
    backtest_results = weights_optimisation.backtest(data, optimised_weights, stock_name)
    if backtest_results[0] < 50:
        return ({}, {}) # do nothing if the current strategy is unlikely to work (has winrate < 50%)
    
    # get current trading signal using the weights
    unweighted_signals = ta_lib.TA(data, weights_optimisation.forex(stock_name))
    Nweights = len(unweighted_signals.iloc[0]) # number of weights required according to ta_lib.py (basically how many indactors we are using)
    overall_signal = 0
    for i in range(Nweights):
        overall_signal += optimised_weights[i]*unweighted_signals.iloc[0][i] # apply the weights

    # make the decisions based on the same thresholds used in weights_optimisation.py
    if overall_signal > 0.4:
        # price predicted to go up
        # print ('Buy a call at '+str(current_data['Datetime']))
        stoploss = current_data['Close']-current_data['ATR']*2
        takeprofit = current_data['Close']+current_data['ATR']*2.5
        """
        Execute trade here? app.buy(call)
        Or we can just have the optionsTA.py file read the suggested trade actions in the log file and see if got any good options?
        """
        # write trade actions to a file
        parent_dire = 'Trade-action-logs/'
        filename = current_date + '_' + stock_name +'_call-logs.txt'
        fullpath = os.path.join(parent_dire, filename)

        if not os.path.exists(parent_dire):
            os.mkdir(parent_dire)
            
        call_file = open(fullpath, "a+")
        # data is written in the format of transaction timestamp, underlying price at time of purchase, stoploss, takeprofit
        call_file.write(str(current_data['Datetime']) + '\t' + str(current_data['Close']) + '\t' + str(stoploss) + '\t' + str(takeprofit) + '\n')
        call_file.close()
        calls[str(current_data['Datetime'])] = (current_data['Close'], stoploss, takeprofit)

        
    elif overall_signal < -0.4:
        # print('Buy a put at '+str(current_data['Datetime']))
        stoploss = current_data['Close']+current_data['ATR']*2
        takeprofit = current_data['Close']-current_data['ATR']*2.5
        """
        Execute trade here? app.buy(put)
        Or we can just have the optionsTA.py file read the suggested trade actions in the log file and see if got any good options?
        """
        # write trade actions to a file
        parent_dire = 'Trade-action-logs/'
        filename = current_date + '_' + stock_name +'_put-logs.txt'
        fullpath = os.path.join(parent_dire, filename)

        if not os.path.exists(parent_dire):
            os.mkdir(parent_dire)

        put_file = open(fullpath, "a+")
        # data is written in the format of transaction timestamp, underlying price at time of purchase, stoploss, takeprofit
        put_file.write(str(current_data['Datetime']) + '\t' + str(current_data['Close']) + '\t' + str(stoploss) + '\t' + str(takeprofit) + '\n')
        put_file.close()
        puts[str(current_data['Datetime'])] = (current_data['Close'], stoploss, takeprofit)

        """"
        Assume that the stoploss/take profit is set in the broker and it will auto close the position if either one is hit
        """
    print('DONE!!')
    return calls,puts # in case we want to just call this script directly from another python script

def is_time_between(begin_time, end_time, check_time=None): # dun anyhow use i just copied this code from some stack overflow post and it doesnt work with less than 3 args
    # If check time is not given, default to current UTC time
    check_time = check_time or datetime.utcnow().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time
    
def trading_hours(): # check if it is currently trading hours
    return is_time_between(datetime.time(21,30), datetime.time(4,0), datetime.datetime.now().time())

def weights_file_name(stock_name):
    yesterday_date = str(datetime.date.today() - datetime.timedelta(days=1))
    current_date = str(datetime.date.today())
    if not trading_hours():
        current_date = yesterday_date # no new market data yet if not during trading hours so the latest file would have yesterday's date
    weights_filename = 'Optimised-weights/'+current_date + '_' + stock_name +'_optimised-weights.txt'
    return weights_filename

def bad_optimise(stock_name): # detects if optimisation was bad
    weights_filename = weights_file_name(stock_name)
    weights_file = open(weights_filename, "r")
    optimised_weights = []
    optimised_weights_data = csv.reader(weights_file, delimiter='\n')
    for row in optimised_weights_data:
        optimised_weights.append(float(row[0]))
    weights_file.close()
    
    baasly = 0
    if sum(optimised_weights) == baasly: # if the previous optimisation was baasly (no samples with good success rate)
        return True
    else:
        return False

# this is meant to be run outside of trading hours to prepare weights that will be read during trading hours
# and to give a list of tickers we actually want to use
def cleanup(stock_list): # ONLY FOR TESTING PURPOSES! in actaul implementation the decision() function will just retry the optimisation
    good_stock_list = []
    # assuming optimsation was ran before trading hours, on a trading day, and it is STILL before trading hours        
    # OR the optimisation was ran DURING trading hours, and it is STILL trading hours
    for i in stock_list:
        if not os.path.exists(weights_file_name(i)):
            print('Weights file for '+ i +' does not exist!')
            continue
        
        # remove the badly optimised weights file
        if bad_optimise(i):
            print('Removed '+i)
            os.remove(weights_file_name(i))
        else:
            if not trading_hours(): # prepare the weight files to be read the when trading opens
                current_date = str(datetime.date.today())
                new_filename = 'Optimised-weights/'+current_date + '_' + i +'_optimised-weights.txt'
                os.rename(weights_file_name(i), new_filename) # prepare the weight files to be read the when trading opens if it is currently before trading hours
            good_stock_list.append(i)  # add to list of good stocks for trading
    return good_stock_list

"""
example usage for the new cleanup() and function to pre-optimise our data
stock_list = ["SPY", "TSLA", "NVDA", "V", "MA", "AMD", "PYPL", "GME", "PLTR", "MSFT", "GOOGL", "AAPL", "MU", "JPM", "DIS", "NFLX", "MMM", "CAT", "NKE", "WMT", "COST", "CSCO", "PFE", "SSL", "RIOT", "GILD", "AMZN", "BABA"]
for i in stock_list:
    print(decision(i))
stock_list = cleanup(stock_list)

# can use the cleaned stocklist now
for i in stock_list:
    print(decision(i)) # should be fast af
    
"""




# if len(sys.argv) != 4:
#     print("Positional arguments:")
#     print("(i) Ticker name")
#     print("(ii) Data lookback period")
#     print("(iii) Resolution of data")
#     sys.exit()
# else:
#     results = optimise_decision(sys.argv[1], sys.argv[2], sys.argv[3])
#     print(results)
#     sys.exit()

  