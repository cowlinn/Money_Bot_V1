import pandas as pd
import ta_lib
import talib
import yfinance as yf
import weights_optimisation
import sys
import os 

"""
how to call:
    - by importing:
        
        import underlyingTA
        stock_name = 'SPY'
        trades = underlyingTA.decision(stock_name)
        
        or
        
        stock_lst = ['SPY', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'GOOGL', 'NVDA', 'MA', 'V']
        for i in stock_lst:
            underlyingTA.decision(i) # it will just write a bunch of log files
            

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
def decision(stock_name, data_period = '4d', resolution = '15m'):
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
    
    # get optimised weights by backtesting through the data_period. Weights have precision of 0.1
    optimised_weights = weights_optimisation.optimise(data, interval = 0.1, min_sample_size = min_samples)
    backtest_results = weights_optimisation.backtest(data, optimised_weights)
    if backtest_results[0] < 50:
        return 0 # do nothing if the current strategy is unlikely to work (has winrate < 50%)
    
    # get current trading signal using the weights
    unweighted_signals = ta_lib.TA(data)
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
        call_file.write(str(current_data['Datetime']) + '    ' + str(current_data['Close']) + '    ' + str(stoploss) + '    ' + str(takeprofit))
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
        put_file.write(str(current_data['Datetime']) + '    ' + str(current_data['Close']) + '    ' + str(stoploss) + '    ' + str(takeprofit))
        put_file.close()
        puts[str(current_data['Datetime'])] = (current_data['Close'], stoploss, takeprofit)

        """"
        Assume that the stoploss/take profit is set in the broker and it will auto close the position if either one is hit
        """
    print('DONE!!')
    return calls,puts # in case we want to just call this script directly from another python script

if len(sys.argv) != 4:
    print("Positional arguments:")
    print("(i) Ticker name")
    print("(ii) Data lookback period")
    print("(iii) Resolution of data")
    sys.exit()
else:
    results = decision(sys.argv[1], sys.argv[2], sys.argv[3])
    print(results)
    sys.exit()

  