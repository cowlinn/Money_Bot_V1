import pandas as pd
import ta_lib
import talib
import yfinance as yf
import weights_optimisation
import sys
import os 
import csv
import datetime
import underlyingTA_db
# ALL TIMES ARE IN SINGAPORE TIME (GMT +8)
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
def optimise_decision(stock_name, data_period = '4d', resolution = '15m', first = True, threshold = 0.4):
    calls = {}
    puts = {}
    
    # check if trading just opened
    if start_of_day():
        lookback_days = int(data_period[:-1]) + 1
        data_period = str(lookback_days) + 'd' # add 1 aditional day of data if it's still the first half of trading day
    
    # call the data
    stock = yf.Ticker(stock_name)  # this goes in main()
    data = stock.history(period = data_period, interval = resolution) # historical price data
    data.reset_index(inplace=True) # converts datetime to a column
    data['ATR'] = talib.ATR(data['High'].to_numpy(), data['Low'].to_numpy(), data['Close'].to_numpy())
    current_data = data.iloc[-1] 
    current_date = str(data['Datetime'].iloc[-1]).split()[0]
    min_samples = int(data_period[:-1]) # average of 1 trade per day?
    optimisation_interval = 0.01
    if weights_optimisation.forex(stock_name) or not first or trading_hours():
        optimisation_interval = 0.05
    # get optimised weights by backtesting through the data_period. Weights have precision of 0.1
    # changed the precision to 0.01 (it takes about 3 min and 20s to run as compared to 20s for 0.1)
    # at 15m resolution the 3min is not THAT bad considering we only run this like once or twice a day?
    optimised_weights = weights_optimisation.optimise(data, interval = optimisation_interval, min_sample_size = min_samples, stock_name = stock_name, threshold = threshold)
   
    # write optimised weigths to a file
    if trading_hours():
        use_date = current_date
        # parent_dir = 'Optimised-weights/' + current_date +'/'
        # weights_file_name = stock_name +'_optimised-weights.txt'
    elif not trading_hours():
        use_date = str(datetime.date.today())
        # parent_dir = 'Optimised-weights/' + str(datetime.date.today()) +'/'
        # weights_file_name = stock_name +'_optimised-weights.txt'
    # fullpath = os.path.join(parent_dir, weights_file_name)
    # if not os.path.exists(parent_dir):
    #     os.makedirs(parent_dir)
    # instead of writing to a .txt file, we will write the data to a db file
    # weights_file = open(fullpath, "w") # "w" because we only want ONE set of weights at a time for a given ticker on a given trading day
    # assume we want to keep logs of the weights for each day for now, if we dun need can just remove current-date from the filename
    # for i in optimised_weights:
    #     weights_file.write(str(i)+'\n')
    # weights_file.close()
    
    # write to the Optimised-weights.db database
    ID = use_date+stock_name
    dbweights = underlyingTA_db.list_to_string(optimised_weights)
    insert_tuple = (ID, use_date, stock_name, dbweights)
    underlyingTA_db.write_weights_to_db(insert_tuple)
    
    backtest_results = weights_optimisation.backtest(data, optimised_weights, stock_name, threshold = threshold)
    if backtest_results[0] < 0.5:
        return ({}, {}) # do nothing if the current strategy is unlikely to work (has winrate < 50%)
    
    # get current trading signal using the weights
    unweighted_signals = ta_lib.TA(data, weights_optimisation.forex(stock_name))
    Nweights = len(unweighted_signals.iloc[0]) # number of weights required according to ta_lib.py (basically how many indactors we are using)
    overall_signal = 0
    for i in range(Nweights):
        overall_signal += optimised_weights[i]*unweighted_signals.iloc[0][i] # apply the weights

    # make the decisions based on the same thresholds used in weights_optimisation.py
    if overall_signal >= threshold:
        Type = 'CALL'
        # price predicted to go up
        # print ('Buy a call at '+str(current_data['Datetime']))
        stoploss = current_data['Close']-current_data['ATR']*1.5
        takeprofit = current_data['Close']+current_data['ATR']*1.875
        """
        Execute trade here? app.buy(call)
        Or we can just have the optionsTA.py file read the suggested trade actions in the log file and see if got any good options?
        """
        # write trade actions to a file
        # parent_dire = 'Trade-action-logs/' + current_date + '/'
        # filename = stock_name +'_call-logs.txt'
        # fullpath = os.path.join(parent_dire, filename)

        # if not os.path.exists(parent_dire):
        #     os.makedirs(parent_dire)
            
        # call_file = open(fullpath, "a+")
        # # data is written in the format of transaction timestamp, underlying price at time of purchase, stoploss, takeprofit
        # call_file.write(str(current_data['Datetime']) + '\t' + str(current_data['Close']) + '\t' + str(stoploss) + '\t' + str(takeprofit) + '\n')
        # call_file.close()
        
        # write trade actions to a db
        dateTime = str(current_data['Datetime'])
        ID = dateTime+stock_name+Type
        currentPrice = current_data['Close']
        insert_tuple = (ID, Type, use_date, dateTime, stock_name, currentPrice, stoploss, takeprofit)
        underlyingTA_db.write_trade_actions_to_db(insert_tuple)
        
        calls[str(current_data['Datetime'])] = (current_data['Close'], stoploss, takeprofit)

        
    elif overall_signal <= -threshold:
        Type = 'PUT'
        # print('Buy a put at '+str(current_data['Datetime']))
        stoploss = current_data['Close']+current_data['ATR']*1.5
        takeprofit = current_data['Close']-current_data['ATR']*1.875
        """
        Execute trade here? app.buy(put)
        Or we can just have the optionsTA.py file read the suggested trade actions in the log file and see if got any good options?
        """
        # write trade actions to a file
        # parent_dire = 'Trade-action-logs/' + current_date + '/'
        # filename = stock_name +'_put-logs.txt'
        # fullpath = os.path.join(parent_dire, filename)

        # if not os.path.exists(parent_dire):
        #     os.makedirs(parent_dire)

        # put_file = open(fullpath, "a+")
        # # data is written in the format of transaction timestamp, underlying price at time of purchase, stoploss, takeprofit
        # put_file.write(str(current_data['Datetime']) + '\t' + str(current_data['Close']) + '\t' + str(stoploss) + '\t' + str(takeprofit) + '\n')
        # put_file.close()
        
        # write trade actions to a db
        dateTime = str(current_data['Datetime'])
        ID = dateTime+stock_name+Type
        currentPrice = current_data['Close']
        insert_tuple = (ID, Type, use_date, dateTime, stock_name, currentPrice, stoploss, takeprofit)
        underlyingTA_db.write_trade_actions_to_db(insert_tuple)

        puts[str(current_data['Datetime'])] = (current_data['Close'], stoploss, takeprofit)

        """"
        Assume that the stoploss/take profit is set in the broker and it will auto close the position if either one is hit
        """
    print('DONE!!')
    return calls,puts # in case we want to just call this script directly from another python script

# make a trading decision based on current available market information
def decision(stock_name, data_period = '4d', resolution = '15m', threshold = 0.4):

    #TODO: RESOLUTION CANNOT BE 1 MIN IF NOT DEVAX, RMB TO UNDO 
    # CODE BELOW 
    #resolution = "5m"
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
    data['ATR'] = talib.ATR(data['High'].to_numpy(), data['Low'].to_numpy(), data['Close'].to_numpy())
    current_data = data.iloc[-1] 
    current_date = str(data['Datetime'].iloc[-1]).split()[0]
    
    # get optimised weights by reading from file
    if trading_hours():
        use_date = current_date
    elif not trading_hours():
        use_date = str(datetime.date.today())
    readID = use_date+stock_name
    optimised_weights = underlyingTA_db.read_weights_from_db((readID,))
    if optimised_weights is None: # if u call this as the first decision of the day
        print('Performing first optimisation of the day.')
        return optimise_decision(stock_name, data_period, resolution, threshold = threshold)
    # weights_file = open(fullpath, "r") # instead of reading from a .txt, we will read from a db file here
    # optimised_weights = []
    # optimised_weights_data = csv.reader(weights_file, delimiter='\n')
    # for row in optimised_weights_data:
    #     optimised_weights.append(float(row[0]))
    # weights_file.close()
    
    baasly = 0
    if sum(optimised_weights) == baasly: # if the previous optimisation was baasly (no samples with good success rate)
        print('Previous optimisation unsuccessful, retrying optimsation!')
        return optimise_decision(stock_name, data_period, resolution, first = False, threshold = threshold) # run the optimsation again and return the (potentially) new result instead. Also, rewrite the weights file if it is different
    
    backtest_results = weights_optimisation.backtest(data, optimised_weights, stock_name, threshold = threshold)
    if backtest_results[0] < 0.5:
        return ({}, {}) # do nothing if the current strategy is unlikely to work (has winrate < 50%)
    
    # get current trading signal using the weights
    unweighted_signals = ta_lib.TA(data, weights_optimisation.forex(stock_name))
    Nweights = len(unweighted_signals.iloc[0]) # number of weights required according to ta_lib.py (basically how many indactors we are using)
    overall_signal = 0
    for i in range(Nweights):
        overall_signal += optimised_weights[i]*unweighted_signals.iloc[0][i] # apply the weights

    # make the decisions based on the same thresholds used in weights_optimisation.py
    if overall_signal >= threshold:
        Type = 'CALL'
        # price predicted to go up
        # print ('Buy a call at '+str(current_data['Datetime']))
        stoploss = current_data['Close']-current_data['ATR']*1.5
        takeprofit = current_data['Close']+current_data['ATR']*1.875
        """
        Execute trade here? app.buy(call)
        Or we can just have the optionsTA.py file read the suggested trade actions in the log file and see if got any good options?
        """
        dateTime = str(current_data['Datetime'])
        ID = dateTime+stock_name+Type
        currentPrice = current_data['Close']
        insert_tuple = (ID, Type, use_date, dateTime, stock_name, currentPrice, stoploss, takeprofit)
        underlyingTA_db.write_trade_actions_to_db(insert_tuple)


        calls[str(current_data['Datetime'])] = (current_data['Close'], stoploss, takeprofit)

        
    elif overall_signal <= -threshold:
        Type = 'PUT'
        # print('Buy a put at '+str(current_data['Datetime']))
        stoploss = current_data['Close']+current_data['ATR']*1.5
        takeprofit = current_data['Close']-current_data['ATR']*1.875
        """
        Execute trade here? app.buy(put)
        Or we can just have the optionsTA.py file read the suggested trade actions in the log file and see if got any good options?
        """
        dateTime = str(current_data['Datetime'])
        ID = dateTime+stock_name+Type
        currentPrice = current_data['Close']
        insert_tuple = (ID, Type, use_date, dateTime, stock_name, currentPrice, stoploss, takeprofit)
        underlyingTA_db.write_trade_actions_to_db(insert_tuple)

        puts[str(current_data['Datetime'])] = (current_data['Close'], stoploss, takeprofit)

        """"
        Assume that the stoploss/take profit is set in the broker and it will auto close the position if either one is hit
        """
    print('DONE!!\n')
    return calls,puts # in case we want to just call this script directly from another python script

# is the current time between a certain time period?
def is_time_between(begin_time, end_time, current_time = datetime.datetime.now().time()): # dun anyhow use i just copied this code from some stack overflow post and it doesnt work with less than 3 args
    if begin_time < end_time:
        return current_time >= begin_time and current_time <= end_time
    else: # crosses midnight
        return current_time >= begin_time or current_time <= end_time
    
def trading_hours(): # check if it is currently trading hours
    return is_time_between(datetime.time(21,30), datetime.time(4,0))

def start_of_day(): # check if it is currently within the first 3 hours of the trading day
    return is_time_between(datetime.time(21,30), datetime.time(0,45))

# returns the weights_filename the current trading day if we are during trading hours
# or the upcoming trading if we are running before market open
# basically returns the "most relevant" weights file we should be reading
def check_weights(stock_name):
    yesterday_date = str(datetime.date.today() - datetime.timedelta(days=1))
    current_date = str(datetime.date.today())
    if not trading_hours():
        use_date = current_date
    elif trading_hours() and is_time_between(datetime.time(21,30), datetime.time(23,59)):
        use_date = current_date
    elif trading_hours() and is_time_between(datetime.time(0,0), datetime.time(4,5)):
        use_date = yesterday_date
    # try and read the weights
    readID = use_date+stock_name
    optimised_weights = underlyingTA_db.read_weights_from_db((readID,))

    return optimised_weights

def bad_optimise(stock_name): # detects if optimisation was bad
    optimised_weights = check_weights(stock_name)    
    baasly = 0
    if sum(optimised_weights) == baasly: # if the previous optimisation was baasly (no samples with good success rate)
        return True
    else:
        return False

# this is meant to be run outside of trading hours to prepare weights that will be read during trading hours
# and to give a list of tickers we actually want to use
def cleanup(stock_list, retry_optimisation = False, threshold = 0.4): # ONLY FOR TESTING PURPOSES! in actaul implementation the decision() function will just retry the optimisation
    good_stock_list = []
    data = yf.Ticker(stock_list[0]).history(period = '1d', interval = '15m')
    data.reset_index(inplace=True) # converts datetime to a column
    current_date = str(data['Datetime'].iloc[-1]).split()[0]
    if trading_hours():
        use_date  = current_date
    elif not trading_hours():
        use_date = str(datetime.date.today())
    
    read_weights = underlyingTA_db.read_weights_by_date((use_date,))
    # if there has not been ANY optimisation run for that day yet, run optimisation for the list of stocks for that day
    if not read_weights:
        for stock_name in stock_list:
                decision(stock_name, threshold = threshold) # write a weights file

    # _, _, files = next(os.walk(parent_dir))
    # file_count = len(files)
    # if file_count == 0:
    #     for stock_name in stock_list:
    #             decision(stock_name, threshold = threshold) # write a weights file
    existing_weights_list = []
    for entry in read_weights:
        existing_weights_list.append(entry[2]) # append the stock_name that have weights in the db
    # if initial call of decision was not allowed to finish for stock_list, run optimisation for list of stocks
    if len(read_weights) != len(stock_list) and retry_optimisation: # retries optimisation for any stocks that were skipped or was manually terminated
        for stock_name in stock_list:
            if stock_name not in existing_weights_list:
                # for the case where no weights file exists
                decision(stock_name, threshold = threshold) # write a weights file

    # assuming optimsation was ran before trading hours, on a trading day, and it is STILL before trading hours        
    # OR the optimisation was ran DURING trading hours, and it is STILL trading hours
    for stock_name in stock_list:
        if check_weights(stock_name) is None: # look for weights_file dated for TODAY
            print('Weights file for '+ stock_name +' dated for '+str(datetime.date.today())+' does not exist!')
            continue
        
        # remove the badly optimised weights file
        if bad_optimise(stock_name):
            print('Removed '+stock_name)
            removeID = use_date + stock_name
            underlyingTA_db.delete_weights_from_db((removeID,))
        else:
            # if not trading_hours(): # prepare the weight files to be read the when trading opens
            #     current_date = str(datetime.date.today())
            #     new_filename = 'Optimised-weights/'+current_date + '_' + i +'_optimised-weights.txt'
            #     os.rename(weights_file_name(i), new_filename) # prepare the weight files to be read the when trading opens if it is currently before trading hours
            good_stock_list.append(stock_name)  # add to list of good stocks for trading 
    return good_stock_list

"""
# example usage for the new cleanup() and function to pre-optimise our data
stock_list = ["SPY", "TSLA", "NVDA", "V", "MA", "AMD", "PYPL", "GME", "PLTR", "MSFT", "GOOGL", "AAPL", "MU", "JPM", "DIS", "NFLX", "MMM", "CAT", "NKE", "WMT", "COST", "CSCO", "PFE", "SSL", "RIOT", "GILD", "AMZN", "BABA"]
for i in stock_list:
    print(decision(i))
stock_list = cleanup(stock_list)

# can use the cleaned stocklist now
for i in stock_list:
    print(decision(i)) # should be fast af

# when decision() is run outside of trading hours, it will try to read the weights file dated for today, not the last trading day (probably yesterday)
# if the there is no weights file dated for today, it will call the optimisation function to write a weights file dated for today
# if the optimise_decision() function is called outside of trading hours, it will write a weights file dated for the upcoming trading day (assumed to be today)
# if you run during trading hours, it will just use the current trading date

possible scenarios:
1. we want to pre-optimise weights before market opens
# we have some list of stocks to look at
stock_list = ["SPY", "TSLA", "NVDA", "V", "MA", "AMD", "PYPL", "GME", "PLTR", "MSFT", "GOOGL", "AAPL", "MU", "JPM", "DIS", "NFLX", "MMM", "CAT", "NKE", "WMT", "COST", "CSCO", "PFE", "SSL", "RIOT", "GILD", "AMZN", "BABA"]
for i in stock_list:
    print(decision(i)) # prepares a bunch of weights files for the upcoming trading day
# clean the original stock_list to remove any stocks with unsuccessful optimisation.
good_stock_list = cleanup(stock_list)
# use this good_stock_list to trade, leave the original list unaltered in case we want to reoptimise


2. we want to optimise weights at the start of the trading day
# we have some list of stocks to look at
stock_list = ["SPY", "TSLA", "NVDA", "V", "MA", "AMD", "PYPL", "GME", "PLTR", "MSFT", "GOOGL", "AAPL", "MU", "JPM", "DIS", "NFLX", "MMM", "CAT", "NKE", "WMT", "COST", "CSCO", "PFE", "SSL", "RIOT", "GILD", "AMZN", "BABA"]
for i in stock_list:
    print(decision(i)) # instead of printing, execute the decisions here
# clean the original stock_list to remove any stocks with unsuccessful optimisation.
good_stock_list = cleanup(stock_list)
# call the for loop using good_stock_list at 15min intervals to trade
for i in good_stock_list:
    print(decision(i)) # instead of printing, execute the decisions here
# the code is the exact same as scenario 1. but it does different things

3. we want to re-optimise ALL our weights DURING the trading day
# assuming stock_list remained unchanged
for i in stock_list:
    # rewrite all the weights files and execute trades
    print(optimise_decision(i, first = False)) # instead of printing, execute the decisions here
good_stock_list = cleanup(stock_list) # exclude stocks that were still unsueccessful in optimisation
# for subsequent calls, use the good_stock_list
for i in good_stock_list:
    print(decision(i)) # instead of printing, execute the decisions here


4. we want to re-optimise only those that failed pre-optimisation
# assuming stock_list remained unchanged
# assuming cleanup() was done to remove failed optimisation weights files
for i in stock_list:
    # rewrite weights files for stocks that were removed and execute trades
    print(decision(i)) # instead of printing, execute the decisions here
good_stock_list = cleanup(stock_list) # exclude stocks that were still unsueccessful in optimisation
# for subsequent calls, use the good_stock_list
for i in good_stock_list:
    print(decision(i)) # instead of printing, execute the decisions here
# again, the code is the exact same, just need to run the for loop with the initial stock_list if we wanna see if the excluded stocks have any trades



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

  