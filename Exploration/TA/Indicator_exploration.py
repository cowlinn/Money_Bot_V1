import talib as ta
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import math
stock_name = "SPY"
data_period = "30d"
resolution = "5m"
stock = yf.Ticker(stock_name)  # this goes in main()
hist = stock.history(period = data_period, interval = resolution) # historical price data
price = hist['Close']
# NOTE: For some reason (maybe data accuracy), the indicator values do not match up with TradingView's values
# the strategies in TA_strategy_development.txt are written based on tradingview values and thus the thresholds might need to be tweaked a bit

################# price ######################
x_vals = range(len(price))
plt.figure()
plt.title('Price graph for '+ stock_name)
plt.plot(x_vals, price) # blue line
plt.grid()
plt.show()
##############################################

################# RSI ######################
RSI = ta.RSI(price)
rolling_window = 14
RSI_SMA = pd.Series(RSI).rolling(rolling_window).mean() # SMA of RSI over 14 periods

x_vals = range(len(RSI))
plt.figure()
plt.title('RSI graph for '+ stock_name)
plt.plot(x_vals, RSI) # blue line
plt.plot(x_vals, RSI_SMA) # orange line
plt.grid()
plt.show()
##############################################

################# MACD ######################
MACD = ta.MACD(price)
x_vals = range(len(MACD[0]))
plt.figure()
plt.subplot(2,1,1)
plt.title('MACD graph for '+ stock_name)
plt.plot(x_vals, MACD[0]) # blue line
plt.plot(x_vals, MACD[1]) # orange line
plt.grid()

# actual value that we will use (do they call this the signal line?)
plt.subplot(2,1,2)
plt.plot(x_vals, MACD[2])
plt.grid()
plt.show
##############################################

################# MFI ######################
MFI = ta.MFI(hist['High'], hist['Low'], hist['Close'], hist['Volume'], timeperiod = 14)
x_vals = range(len(MFI))
plt.figure()
plt.title('MFI graph for '+ stock_name)
plt.plot(x_vals, MFI) # blue line
plt.grid()
plt.show()
##############################################

hist['RSI'] = RSI
hist['RSI_SMA'] = RSI_SMA
hist['MFI'] = MFI
hist['MACD'] = MACD[2]

################# Overall ######################
x_vals = range(len(MFI))
plt.figure()
plt.subplot(4,1,1)
plt.title('Price graph for '+ stock_name)
plt.plot(x_vals, price) # blue line
plt.grid()

plt.subplot(4,1,3)
plt.title('RSI graph for '+ stock_name)
plt.plot(x_vals, RSI) # blue line
plt.plot(x_vals, RSI_SMA) # orange line
plt.grid()

plt.subplot(4,1,2)
plt.title('MACD graph for '+ stock_name)
plt.plot(x_vals, MACD[0]) # blue line
plt.plot(x_vals, MACD[1]) # orange line
plt.grid()

plt.subplot(4,1,4)
plt.title('MFI graph for '+ stock_name)
plt.plot(x_vals, MFI) # blue line
plt.grid()
plt.tight_layout()
plt.show()
##############################################

################# Backtest ######################
def checkwin(option, movement, threshold = 0.5, silent = False):
    # note: the threshold should be determined by delta of the option
    if option == 'Call':
        if movement > 0 and abs(movement) > threshold:
            if not silent:
                print('Good Trade!\n')
            return True
        else:
            if not silent:
                print('Bad Trade!\n')
            return False
    if option == 'Put':
        if movement < 0  and abs(movement) > threshold:
            if not silent:
                print('Good Trade!\n')
            return True
        else:
            if not silent:
                print('Bad Trade!\n')
            return False

put_buying_threshold = 45
call_buying_threshold = 40
threshold = 0.5 # minimum magnitude of price movement we are trying to capture
purchase_time = 0
underlying_purchase_price = 0
underlying_selling_price = 0
wins = 0
losses = 0
total_movement = 0
total_trade_time = 0
p_time = 0
trade_time_hour = 0
call = False
put = False
hist.reset_index(inplace=True) # converts datetime to a column
for i in range(40, len(hist)):
    current_data = hist.iloc[i]
    previous_data = hist.iloc[i-1]
    current_hour = int(str(current_data['Datetime']).split()[1][0:2])
    current_minute = int(str(current_data['Datetime']).split()[1][3:5])
    # print(current_hour, current_data['Datetime'])
    # print(put, current_hour, current_data['RSI'],current_data['MFI'])
    
    # close any open poisition by end of day
    if call and current_hour > 14 and current_minute > 45:
        call = False
        print('It is currently ' + str(current_data['Datetime']) + '. Sell the call purchased at ' + str(purchase_time))
        underlying_selling_price = current_data['Close']
        movement = round(underlying_selling_price-underlying_purchase_price, 2)
        total_movement += abs(movement)
        trade_time_hour = current_hour-p_time[0] + (current_minute-p_time[1])/60
        total_trade_time += trade_time_hour
        print(str(movement)+' dollars of price movement captured')
        if checkwin('Call', movement, threshold):
            wins += 1
        else:
            losses += 1

    if put and current_hour > 14 and current_minute > 45:
        put = False
        print('It is currently ' + str(current_data['Datetime']) + '. Sell the put purchased at ' + str(purchase_time))
        underlying_selling_price = current_data['Close']
        movement = round(underlying_selling_price-underlying_purchase_price, 2)
        total_movement += abs(movement)
        trade_time_hour = current_hour-p_time[0] + (current_minute-p_time[1])/60
        total_trade_time += trade_time_hour
        print(str(movement)+' dollars of price movement captured')
        if checkwin('Put', movement, threshold):
            wins += 1
        else:
            losses += 1

    if current_hour > 13: # do not enter trades after 2pm
        # print(current_data['Datetime'])
        continue
    
    if current_data['MACD'] > 0 and previous_data['MACD'] < 0 and call == False:
        print('\nUpwards cross at', current_data['Datetime'])
        if current_data['RSI_SMA'] < 45 and current_data['MFI'] < call_buying_threshold:
            print('Buy a Call!\n')
            call = True
            purchase_time = current_data['Datetime']
            p_time = (current_hour, current_minute)
            underlying_purchase_price = current_data['Close']
        
        # exit the position if opposite crossover happens
        # if put:
        #     put = False
        #     print('It is currently ' + str(current_data['Datetime']) + '. Sell the put purchased at ' + str(purchase_time))
        #     underlying_selling_price = current_data['Close']
        #     movement = round(underlying_selling_price-underlying_purchase_price, 2)
        #     total_movement += abs(movement)
        #     trade_time_hour = current_hour-p_time[0] + (current_minute-p_time[1])/60
        #     total_trade_time += trade_time_hour
        #     print(str(movement)+' dollars of price movement captured')
        #     if checkwin('Put', movement, threshold):
        #         wins += 1
        #     else:
        #         losses += 1
            continue
        # aparently not doing this gives a better winrate wtf


    if current_data['MACD'] < 0 and previous_data['MACD'] > 0 and put == False:
        print('\nDownwards cross at', current_data['Datetime'])
        if current_data['RSI_SMA'] > 55 and current_data['MFI'] > put_buying_threshold: # using the talib MFI, 45 is the best threshold
            print('Buy a Put!\n')
            put = True
            purchase_time = current_data['Datetime']
            p_time = (current_hour, current_minute)
            underlying_purchase_price = current_data['Close']
        
        # exit the position if opposite crossover happens
        # if call:
        #     call = False
        #     print('It is currently ' + str(current_data['Datetime']) + '. Sell the call purchased at ' + str(purchase_time))
        #     underlying_selling_price = current_data['Close']
        #     movement = round(underlying_selling_price-underlying_purchase_price, 2)
        #     total_movement += abs(movement)
        #     trade_time_hour = current_hour-p_time[0] + (current_minute-p_time[1])/60
        #     total_trade_time += trade_time_hour
        #     print(str(movement)+' dollars of price movement captured')
        #     if checkwin('Call', movement, threshold):
        #         wins += 1
        #     else:
        #         losses += 1
        continue
        # aparently not doing this gives a better winrate wtf

            
    if call and current_data['RSI'] > 60 and current_data['MFI'] > 65:
        print('It is currently ' + str(current_data['Datetime']) + '. Sell the call purchased at ' + str(purchase_time))
        call = False
        underlying_selling_price = current_data['Close']
        movement = round(underlying_selling_price-underlying_purchase_price, 2)
        total_movement += abs(movement)
        trade_time_hour = current_hour-p_time[0] + (current_minute-p_time[1])/60
        total_trade_time += trade_time_hour
        print(str(movement)+' dollars of price movement captured')
        if checkwin('Call', movement, threshold):
            wins += 1
        else:
            losses += 1

            
    if put and current_data['RSI'] < 40 and current_data['MFI'] < 35:
        print('It is currently ' + str(current_data['Datetime']) + '. Sell the put purchased at ' + str(purchase_time))
        put = False
        underlying_selling_price = current_data['Close']
        movement = round(underlying_selling_price-underlying_purchase_price, 2)
        total_movement += abs(movement)
        trade_time_hour = current_hour-p_time[0] + (current_minute-p_time[1])/60
        total_trade_time += trade_time_hour
        print(str(movement)+' dollars of price movement captured')
        if checkwin('Put', movement, threshold):
            wins += 1
        else:
            losses += 1
    # print(trade_time_hour)

winrate = round((wins/(wins + losses))*100, 2)
total_trades = wins + losses
mean_movement = round(total_movement/total_trades, 2)
mean_trade_time = round(total_trade_time/total_trades, 2)
mean_trade_time_minute = round(mean_trade_time%1 * 60)
mean_trade_time_hour = math.floor(mean_trade_time)
# print(total_trade_time)
print('\nWinrate of ' + str(winrate)+'% across', total_trades,'trades')
print('Average magnitude of price movement captured is $' + str(mean_movement))
print('Average trade duration is', mean_trade_time_hour, 'hour(s) and ', mean_trade_time_minute, 'minutes')

############ callable function ####################
def backtest(hist, threshold = 0.5, call_buying_threshold = 40, put_buying_threshold = 45, call_selling_threshold = 65, put_selling_threshold = 35, rsi_buy = 45, rsi_sell = 60, cross_stop = False, silent = True):
    purchase_time = 0
    underlying_purchase_price = 0
    underlying_selling_price = 0
    wins = 0
    losses = 0
    total_movement = 0
    total_trade_time = 0
    p_time = 0
    trade_time_hour = 0
    call = False
    put = False
    # hist.reset_index(inplace=True) # converts datetime to a column
    for i in range(40, len(hist)):
        current_data = hist.iloc[i]
        previous_data = hist.iloc[i-1]
        current_hour = int(str(current_data['Datetime']).split()[1][0:2])
        current_minute = int(str(current_data['Datetime']).split()[1][3:5])
        # print(current_hour, current_data['Datetime'])
        # print(put, current_hour, current_data['RSI'],current_data['MFI'])
        
        # close any open poisition by end of day
        if call and current_hour > 14 and current_minute > 45:
            call = False
            underlying_selling_price = current_data['Close']
            movement = round(underlying_selling_price-underlying_purchase_price, 2)
            total_movement += movement
            trade_time_hour = current_hour-p_time[0] + (current_minute-p_time[1])/60
            total_trade_time += trade_time_hour
            if not silent:
                print('It is currently ' + str(current_data['Datetime']) + '. Sell the call purchased at ' + str(purchase_time))
                print(str(movement)+' dollars of price movement captured')
            if checkwin('Call', movement, threshold, silent):
                wins += 1
            else:
                losses += 1

        if put and current_hour > 14 and current_minute > 45:
            put = False
            underlying_selling_price = current_data['Close']
            movement = round(underlying_selling_price-underlying_purchase_price, 2)
            trade_time_hour = current_hour-p_time[0] + (current_minute-p_time[1])/60
            total_trade_time += trade_time_hour
            if not silent:
                print('It is currently ' + str(current_data['Datetime']) + '. Sell the put purchased at ' + str(purchase_time))
                print(str(movement)+' dollars of price movement captured')
            if checkwin('Put', movement, threshold, silent):
                wins += 1
                total_movement += abs(movement)
            else:
                losses += 1
                total_movement -= movement

        if current_hour > 13: # do not enter trades after 2pm
            # print(current_data['Datetime'])
            continue
        
        if current_data['MACD'] > 0 and previous_data['MACD'] < 0 and call == False:
            if not silent:
                print('\nUpwards cross at', current_data['Datetime'])
            if current_data['RSI_SMA'] < rsi_buy and current_data['MFI'] < call_buying_threshold:
                if not silent:
                    print('Buy a Call!\n')
                call = True
                purchase_time = current_data['Datetime']
                p_time = (current_hour, current_minute)
                underlying_purchase_price = current_data['Close']
            
            # exit the position if opposite crossover happens
            if cross_stop and put:
                put = False
                underlying_selling_price = current_data['Close']
                movement = round(underlying_selling_price-underlying_purchase_price, 2)
                trade_time_hour = current_hour-p_time[0] + (current_minute-p_time[1])/60
                total_trade_time += trade_time_hour
                if not silent:
                    print('It is currently ' + str(current_data['Datetime']) + '. Sell the put purchased at ' + str(purchase_time))
                    print(str(movement)+' dollars of price movement captured')
                if checkwin('Put', movement, threshold, silent):
                    wins += 1
                    total_movement += abs(movement)
                else:
                    losses += 1
                    total_movement -= movement
                continue
            # aparently not doing this gives a better winrate wtf


        if current_data['MACD'] < 0 and previous_data['MACD'] > 0 and put == False:
            if not silent:
                print('\nDownwards cross at', current_data['Datetime'])
            if current_data['RSI_SMA'] > 100-rsi_buy and current_data['MFI'] > put_buying_threshold: # using the talib MFI, 45 is the best threshold
                if not silent:    
                    print('Buy a Put!\n')
                put = True
                purchase_time = current_data['Datetime']
                p_time = (current_hour, current_minute)
                underlying_purchase_price = current_data['Close']
            
            # exit the position if opposite crossover happens
            if cross_stop and call:
                call = False
                underlying_selling_price = current_data['Close']
                movement = round(underlying_selling_price-underlying_purchase_price, 2)
                total_movement += movement
                trade_time_hour = current_hour-p_time[0] + (current_minute-p_time[1])/60
                total_trade_time += trade_time_hour
                if not silent:
                    print('It is currently ' + str(current_data['Datetime']) + '. Sell the call purchased at ' + str(purchase_time))
                    print(str(movement)+' dollars of price movement captured')
                if checkwin('Call', movement, threshold, silent):
                    wins += 1
                else:
                    losses += 1
            continue
            # aparently not doing this gives a better winrate wtf

                
        if call and current_data['RSI'] > rsi_sell and current_data['MFI'] > call_selling_threshold:
            call = False
            underlying_selling_price = current_data['Close']
            movement = round(underlying_selling_price-underlying_purchase_price, 2)
            total_movement += movement
            trade_time_hour = current_hour-p_time[0] + (current_minute-p_time[1])/60
            total_trade_time += trade_time_hour
            if not silent:
                print('It is currently ' + str(current_data['Datetime']) + '. Sell the call purchased at ' + str(purchase_time))
                print(str(movement)+' dollars of price movement captured')
            if checkwin('Call', movement, threshold, silent):
                wins += 1
            else:
                losses += 1

                
        if put and current_data['RSI'] < 100-rsi_sell and current_data['MFI'] < put_selling_threshold:
            put = False
            underlying_selling_price = current_data['Close']
            movement = round(underlying_selling_price-underlying_purchase_price, 2)
            total_movement += abs(movement)
            trade_time_hour = current_hour-p_time[0] + (current_minute-p_time[1])/60
            total_trade_time += trade_time_hour
            if not silent:
                print('It is currently ' + str(current_data['Datetime']) + '. Sell the put purchased at ' + str(purchase_time))
                print(str(movement)+' dollars of price movement captured')
            if checkwin('Put', movement, threshold, silent):
                wins += 1
                total_movement += abs(movement)
            else:
                losses += 1
                total_movement -= movement
        # print(trade_time_hour)

    
    total_trades = wins + losses
    if total_trades == 0:
        return 0, total_trades
    winrate = round((wins/(wins + losses))*100, 2)
    mean_movement = round(total_movement/total_trades, 2)
    mean_trade_time = round(total_trade_time/total_trades, 2)
    mean_trade_time_minute = round(mean_trade_time%1 * 60)
    mean_trade_time_hour = math.floor(mean_trade_time)
    # print(total_trade_time)
    if not silent:
        print('\nWinrate of ' + str(winrate)+'% across', total_trades,'trades')
        print('Average correct direction of price movement captured is $' + str(mean_movement))
        print('Average trade duration is', mean_trade_time_hour, 'hour(s) and ', mean_trade_time_minute, 'minutes')
    return winrate, total_trades

# WARNING: if extensive_test is True, number of iterations will be (end_range-start_range)**2**2**2**2
# note: it takes forever to train if start_range=10 and end_range=90
# but the result is (13, 89) with literally 1 trade in 30 days
# others with 100% win: all the x,89 ones, 
# could probably give an option to iterate in intervals of 2 or 5 to shorten training time
# aside from that, the best params for the options buying threshold are (40, 89) with 90% winrate and 10 trades in 30 days
# for statistical significance, we should probably stick with (40, 45) with 63% winrate and 30 trades in 30 days

# after adding buying thresholds
# ok final best extensive test for start_range = 35, end_range = 65, interval = 5 is (40, 45, 35, 35)
# can probably add in RSI threshold optimisation also?

# after adding rsi thresholds
# ok rael final extensive test for start_range = 35, end_range = 65, interval = 5 is (40, 45, 35, 35, 45, 60)
def iterative_test(hist, start_range = 35, end_range = 65, extensive_test = False, interval=1):
    hist.reset_index(inplace=True) # converts datetime to a column
    test_log = {}
    iterr = range(start_range,end_range+1,interval)
    if extensive_test:
        test_log = {}
        for i in iterr:
            for k in iterr:
                for a in iterr:
                    for b in iterr:
                        for c in iterr:
                            for d in iterr:
                                test_log[(i,k, a, b, c, d)] = backtest(hist, put_buying_threshold = k, call_buying_threshold = i, call_selling_threshold=a, put_selling_threshold=b, rsi_buy = c, rsi_sell = d)[0]
        best_threshold = max(test_log, key = test_log.get)
        return(best_threshold)

    # find the best put_buying_threshold
    for i in iterr:
        test_log[i] = backtest(hist, put_buying_threshold = i)[0]
    best_put_buying_threshold = max(test_log, key = test_log.get)
    
    # find the best call_buying_threshold
    test_log = {}
    for i in iterr:
        test_log[i] = backtest(hist, call_buying_threshold = i)[0]
    best_call_buying_threshold = max(test_log, key = test_log.get)

    # find the best call_selling_threshold
    test_log = {}
    for i in iterr:
        test_log[i] = backtest(hist, call_selling_threshold = i)[0]
    best_call_selling_threshold = max(test_log, key = test_log.get)
    
    # find the best put_selling_threshold
    test_log = {}
    for i in iterr:
        test_log[i] = backtest(hist, put_selling_threshold = i)[0]
    best_put_selling_threshold = max(test_log, key = test_log.get)
    
    # find the best rsi_buy
    test_log = {}
    for i in iterr:
        test_log[i] = backtest(hist, rsi_buy = i)[0]
    best_rsi_buy = max(test_log, key = test_log.get)

    # find the best rsi_sell
    test_log = {}
    for i in iterr:
        test_log[i] = backtest(hist, rsi_sell = i)[0]
    best_rsi_sell = max(test_log, key = test_log.get)

    return (best_call_buying_threshold, best_put_buying_threshold, best_call_selling_threshold, best_put_selling_threshold, best_rsi_buy, best_rsi_sell)



################# backtest results ##################
# 5 min data, spy, 30 days of data
# note: the MFI from TAlib is FUCKED so use with caution
# just proof of concept for now
# maybe can try not considering MFI?
# nope, I tried already, it is absolutely terrible

# TEST 1: MFI put buying threshold 70 call buying threshold 40
# everything active:
    # Winrate of 52.38% across 21 trades
    # Average magnitude of price movement captured is $1.04
    # Average trade duration is 1 hour(s) and  55 minutes
# stay in a position even if opposite crossover happens, only can make one trade at a time:
    # Winrate of 50.0% across 20 trades
    # Average magnitude of price movement captured is $1.21
    # Average trade duration is 3 hour(s) and  6 minutes


# TEST 2: MFI put buying threshold 45 call buying threshold 40
# everything active:
    # Winrate of 50.0% across 38 trades
    # Average magnitude of price movement captured is $1.08
    # Average trade duration is 1 hour(s) and  37 minutes
# stay in a position even if opposite crossover happens, only can make one trade at a time:
    # Winrate of 63.33% across 30 trades
    # Average magnitude of price movement captured is $1.41
    # Average trade duration is 2 hour(s) and  55 minutes