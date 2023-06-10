import pandas as pd
import ta_lib
import talib
import yfinance as yf

"""
how to call:
    initial = initial_optimise(data, interval = 0.1)
    second = second_optimise(data, interval = 0.1, fixed_weight = initial[0], weight_number = initial[1])

for rael bot:
    just take the optimised weights, copy the code in backtest and just take the latest readings to output some trade action (repplace the buy/sell prints)

Some Results:
- the usefulness of each indicator varies wildly??
- we cannot just optimise for winrate - if the losses are much larger than the wins, we will still loose money
- we may need one more optimisation function?
- two optimised results (backtest(data, 0.125, 0, 0.125, 0.5, 0.125) and backtest(data, 0.1, 0.1, 0.4, 0.3, 0.1))
  gave identical winrates but very different gains, for the same number of trades over 10 days
- using 30 days of 15m data, backtest(data, 0.1, 0.3, 0.3, 0, 0.3) gives an insane result of (74.36, 56.2188720703125, 39)
  74% winrate over 39 trades plus a HUGE gain??
"""

stock_name = "SPY"
data_period = "30d"
resolution = "15m"
stock = yf.Ticker(stock_name)  # this goes in main()
data = stock.history(period = data_period, interval = resolution) # historical price data

test = []
def backtest(data, weight1 = 0.2, weight2 = 0.2, weight3 = 0.2, weight4 = 0.2, weight5 = 0.2):
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
        current_hour = int(str(current_data['Datetime']).split()[1][0:2])
        current_minute = int(str(current_data['Datetime']).split()[1][3:5])
        current = ta_lib.TA(data.loc[:i])
        output = weight1*current.iloc[0][0] + weight2*current.iloc[0][1]+weight3*current.iloc[0][2]+weight4*current.iloc[0][3]+weight5*current.iloc[0][4]
        # if current_hour > 13: # do not enter trades after 2pm
        #     # print(current_data['Datetime'])
        #     continue
        # opening positions
        if output > 0.3:
            # print ('Buy a call at '+str(current_data['Datetime']))
            stoploss = current_data['Close']-current_data['ATR']*1.75
            takeprofit = current_data['Close']+current_data['ATR']*2
            calls[str(current_data['Datetime'])] = (current_data['Close'], stoploss, takeprofit)
            total_trades += 1
        elif output < -0.3:
            # print('Buy a put at '+str(current_data['Datetime']))
            stoploss = current_data['Close']+current_data['ATR']*1.75
            takeprofit = current_data['Close']-current_data['ATR']*2
            puts[str(current_data['Datetime'])] = (current_data['Close'], stoploss, takeprofit)
            total_trades += 1
        
        # closing positions
        remove = []
        for i in calls:
            trade_info = calls[i]
            if current_data['Close'] < trade_info[1]:
                # stoploss triggered, close the position
                losses += 1
                gains += current_data['Close']-trade_info[0] # count the profit/loss
                print('It is currently ' + str(current_data['Datetime']) + '. Sell the call purchased at ' + i)
                print(trade_info[0]-current_data['Close'] ,'baaasly trade')
                remove.append(i)
            elif current_data['Close'] > trade_info[2]:
                # takeprofit reached, close the position
                wins += 1
                gains += current_data['Close']-trade_info[0] # count the profit/loss
                print('It is currently ' + str(current_data['Datetime']) + '. Sell the call purchased at ' + i)
                print(current_data['Close']-trade_info[0],'guuuud trade')
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
                print('It is currently ' + str(current_data['Datetime']) + '. Sell the put purchased at ' + i)
                print(trade_info[0]-current_data['Close'] ,'guuuud trade')
                remove.append(i)
            elif current_data['Close'] > trade_info[1]:
                # stoploss triggered, close the position
                losses += 1
                gains += trade_info[0]-current_data['Close'] # count the profit/loss
                print('It is currently ' + str(current_data['Datetime']) + '. Sell the put purchased at ' + i)
                print(trade_info[0]-current_data['Close'] ,'baaasly trade')
                remove.append(i)
        for i in remove:
                # remove closed positions from dictionary of open positions
                puts.pop(i)
    completed_trades = wins + losses
    if completed_trades == total_trades:
        print('All trades completed')
    winrate = round(wins/completed_trades*100, 2)
    return winrate, gains, completed_trades #, calls, puts

def initial_optimise(data, interval, Nweights = 5, min_sample_size = 15):
    test_log = {}
    iterr = range(0,int(1/interval))
    #Nweights = 5 # number of weights
    for i in iterr:
        test_weight = i*interval
        normalised_weights = (1-test_weight)/(Nweights-1) # distribute the remaining weight equally
        name1 = str(test_weight)+' 1'
        name2 = str(test_weight)+' 2'
        name3 = str(test_weight)+' 3'
        name4 = str(test_weight)+' 4'
        name5 = str(test_weight)+' 5'
        result1 = backtest(data, test_weight, normalised_weights, normalised_weights, normalised_weights, normalised_weights)
        result2 = backtest(data, normalised_weights, test_weight, normalised_weights, normalised_weights, normalised_weights)
        result3 = backtest(data, normalised_weights, normalised_weights, test_weight, normalised_weights, normalised_weights)
        result4 = backtest(data, normalised_weights, normalised_weights, normalised_weights, test_weight, normalised_weights)
        result5 = backtest(data, normalised_weights, normalised_weights, normalised_weights, normalised_weights, test_weight)
        # only add significant samples to find highest winrate
        if result1[2] > min_sample_size:
            test_log[name1] = result1[0]
        if result2[2] > min_sample_size:
            test_log[name2] = result2[0]
        if result3[2] > min_sample_size:
            test_log[name3] = result3[0]
        if result4[2] > min_sample_size:
            test_log[name4] = result4[0]
        if result5[2] > min_sample_size:
            test_log[name5] = result5[0]
    best_weight = max(test_log, key = test_log.get)
    result = best_weight.split()
    result[0] = float(result[0])
    result[1] = int(result[1])
    return result

def second_optimise(data, interval, fixed_weight, weight_number, min_sample_size = 15):
    test_log = {}
    iterr = range(0,int((1-fixed_weight)/interval)+1)
    for i in iterr:
        test_weight = i*interval
        normalised_weights = (1-test_weight-fixed_weight)/3
        
        if weight_number == 1:
            name2 = str(test_weight)+' 2'
            name3 = str(test_weight)+' 3'
            name4 = str(test_weight)+' 4'
            name5 = str(test_weight)+' 5'
            result2 = backtest(data, fixed_weight, test_weight, normalised_weights, normalised_weights, normalised_weights)
            result3 = backtest(data, fixed_weight, normalised_weights, test_weight, normalised_weights, normalised_weights)
            result4 = backtest(data, fixed_weight, normalised_weights, normalised_weights, test_weight, normalised_weights)
            result5 = backtest(data, fixed_weight, normalised_weights, normalised_weights, normalised_weights, test_weight)
            if result2[2] > min_sample_size:
                test_log[name2] = result2[0]
            if result3[2] > min_sample_size:
                test_log[name3] = result3[0]
            if result4[2] > min_sample_size:
                test_log[name4] = result4[0]
            if result5[2] > min_sample_size:
                test_log[name5] = result5[0]

        if weight_number == 2:
            name1 = str(test_weight)+' 1'
            name3 = str(test_weight)+' 3'
            name4 = str(test_weight)+' 4'
            name5 = str(test_weight)+' 5'
            result1 = backtest(data, test_weight, fixed_weight, normalised_weights, normalised_weights, normalised_weights)
            result3 = backtest(data, normalised_weights, fixed_weight, test_weight, normalised_weights, normalised_weights)
            result4 = backtest(data, normalised_weights, fixed_weight, normalised_weights, test_weight, normalised_weights)
            result5 = backtest(data, normalised_weights, fixed_weight, normalised_weights, normalised_weights, test_weight)
            if result1[2] > min_sample_size:
                test_log[name1] = result1[0]
            if result3[2] > min_sample_size:
                test_log[name3] = result3[0]
            if result4[2] > min_sample_size:
                test_log[name4] = result4[0]
            if result5[2] > min_sample_size:
                test_log[name5] = result5[0]

        if weight_number == 3:
            name1 = str(test_weight)+' 1'
            name2 = str(test_weight)+' 2'
            name4 = str(test_weight)+' 4'
            name5 = str(test_weight)+' 5'
            result1 = backtest(data, test_weight, normalised_weights, fixed_weight, normalised_weights, normalised_weights)
            result2 = backtest(data, normalised_weights, test_weight, fixed_weight, normalised_weights, normalised_weights)
            result4 = backtest(data, normalised_weights, normalised_weights, fixed_weight, test_weight, normalised_weights)
            result5 = backtest(data, normalised_weights, normalised_weights, fixed_weight, normalised_weights, test_weight)
            if result1[2] > min_sample_size:
                test_log[name1] = result1[0]
            if result2[2] > min_sample_size:
                test_log[name2] = result2[0]
            if result4[2] > min_sample_size:
                test_log[name4] = result4[0]
            if result5[2] > min_sample_size:
                test_log[name5] = result5[0]

        if weight_number == 4:
            name1 = str(test_weight)+' 1'
            name2 = str(test_weight)+' 2'
            name3 = str(test_weight)+' 3'
            name5 = str(test_weight)+' 5'
            result1 = backtest(data, test_weight, normalised_weights, normalised_weights, fixed_weight, normalised_weights)
            result2 = backtest(data, normalised_weights, test_weight, normalised_weights, fixed_weight, normalised_weights)
            result3 = backtest(data, normalised_weights, normalised_weights, test_weight, fixed_weight, normalised_weights)
            result5 = backtest(data, normalised_weights, normalised_weights, normalised_weights, fixed_weight, test_weight)
            if result1[2] > min_sample_size:
                test_log[name1] = result1[0]
            if result2[2] > min_sample_size:
                test_log[name2] = result2[0]
            if result3[2] > min_sample_size:
                test_log[name3] = result3[0]
            if result5[2] > min_sample_size:
                test_log[name5] = result5[0]
    
        if weight_number == 5:
            name1 = str(test_weight)+' 1'
            name2 = str(test_weight)+' 2'
            name3 = str(test_weight)+' 3'
            name4 = str(test_weight)+' 4'
            result1 = backtest(data, test_weight, normalised_weights, normalised_weights, normalised_weights, fixed_weight)
            result2 = backtest(data, normalised_weights, test_weight, normalised_weights, normalised_weights, fixed_weight)
            result3 = backtest(data, normalised_weights, normalised_weights, test_weight, normalised_weights, fixed_weight)
            result4 = backtest(data, normalised_weights, normalised_weights, normalised_weights, test_weight, fixed_weight)
            if result1[2] > min_sample_size:
                test_log[name1] = result1[0]
            if result2[2] > min_sample_size:
                test_log[name2] = result2[0]
            if result3[2] > min_sample_size:
                test_log[name3] = result3[0]
            if result4[2] > min_sample_size:
                test_log[name4] = result4[0]
    best_weight = max(test_log, key = test_log.get)
    print(test_log[best_weight], best_weight)
    second_lst = best_weight.split()
    second_lst[0] = float(second_lst[0])
    second_lst[1] = int(second_lst[1])
    second = [(fixed_weight, weight_number), tuple(second_lst)]
    return second
       


