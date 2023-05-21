# -*- coding: utf-8 -*-
"""
Created on Mon Apr 17 14:04:18 2023

@author: Darryl
"""
# to do: implement weighted average median (similar thing to the sdprop function but for median and IQR so we can look at stocks with skewed distributions)
# function needs to take in stock_info and output buying ratio (by minimising IQR or lower bound?) and upper/lower bound
# backtesting function

# what useful comparison can I get? what do I want the script to do? reccomend an ideal portfolio that combines the stocks?
# maybe it can say which stock has the highest mean, which stock has highest median? but that isn't very useful
# maybe just print all the stock_info data formatted properly
# answer the question of how should I split x amount of money among a list of stocks to minimise risk
# how many ways can I split x amount of money? infinty
# well maybe I can do it like a fraction because it's not feasible to buy let's say $10 of apple stock
# so we can just let smallest percentage be 1%? huh means u need 10+ thousand to invest or should it be 10%
# ok 1%
# risk = potential losses
# formula for risk: y = a*x1 + b*x2 + ...
# xn is the potential loss (lower bound) for stock n, a, b etc is the proportion of portfolio such that a + b + c + ... = 1
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd  # do I even need these??
import numpy as np

def stock_eval(stock_name, investment_period, historical_range): # evaluate mean, median, SD, Q1 and Q3 for a stock
    # stock name is a string, investment_period is in days and historical_range should be in y or mo
    stock = yf.Ticker(stock_name)
    trading_days = round(investment_period*252/365) # converts real time into trading days
    hist = stock.history(period = historical_range, interval = "1d")
    data = hist[["Close"]]
    prev_price = data.shift(trading_days) # compares price to one (investment period) ago
    increase = data-prev_price # asks the question of "at this point in history, if I had held the stock for a year, what would be my return?"
    percentage_increase = increase/prev_price*100
    percentage_increase = percentage_increase.dropna()
    
    # for symmetric data
    mean=percentage_increase.mean() #HUH I COULD HAVE JUST USED THIS
    sd = percentage_increase.std() #lmao could have just used this or .var()

    # for skewed data
    median = percentage_increase.median()
    Q1 = percentage_increase["Close"].quantile(0.25)
    Q3 = percentage_increase["Close"].quantile(0.75)
    
    # plots the price changes for each investment period interval
    plt.hist(percentage_increase["Close"], bins=30)
    plt.title(stock_name)
    plt.xlabel('Percentage Increase')
    plt.ylabel('Frequency')
    plt.show()
    
    return (mean["Close"], median["Close"], sd["Close"], Q1, Q3, percentage_increase)

def sdprop(stock_info):   # returns a reccomended buying ratio and resultant SD according to minimisation of SD
    sdrisk = []
    ratios = []
    proportion = 1/len(stock_info)
    for stock in range(len(stock_info)):
        varstocksd = []
        otherstocks = [list(ele) for ele in stock_info]
        otherstocks.remove(otherstocks[stock])
        stockSD = stock_info[stock][2]
        # start each stock with 1/len(all_stocks) proportion then pick the first stock, decrease its proportion to 1% and increase the others at an equal rate
        # find the smallest value by increasing from 1% to 100% and that will be the fixed proportion for that stock
        # repeat for all stocks
        # can change the minimum percent by changing the range of this for loop
        for r in range(99):
            ratio = (r+1)/100
            sharelost = proportion - ratio # max of 100 stocks to balance
            # share lost is to be distributed among the other stocks equally
            distribute = sharelost/(len(stock_info)-1)
            otherratio = distribute + proportion
            y = (stockSD*ratio)**2
            for i in range(len(otherstocks)):
                y += (otherratio*otherstocks[i][2])**2
            SDrisk = y**(1/2)
            varstocksd.append(SDrisk)
        sdrisk.append(varstocksd)
    
    for r in range(len(stock_info)):
        minvalue = min(sdrisk[r])
        index = sdrisk[r].index(minvalue) + 1
        ratios.append(index)
    normratios = []
    sumsq = 0
    for n in range(len(ratios)):
        normratios.append(round(ratios[n]/sum(ratios), 3))
    for i in range(len(normratios)):
        sumsq += (normratios[i]*stock_info[i][2])**2
    Y = sumsq**(1/2)
    return(normratios, Y)

def print_info(all_stocks, investment_period, historical_range, stock_info): # prints stock information calculated by stock_eval for all the stocks
    for i in range(len(all_stocks)):
        high = stock_info[i][0] + stock_info[i][2]
        low = stock_info[i][0] - stock_info[i][2]
        print ("\nThe following results are obtained by considering historial data over a period of the past", historical_range)
        print("The mean percentage gain of ", all_stocks[i], " over ", investment_period, " days is ", round(stock_info[i][0], 2),"%")
        print("The median percentage gain of ", all_stocks[i], " over ", investment_period, " days is ", round(stock_info[i][1], 2),"%")
        print("Based on SD, the upper bound is ", round(high, 2), "% and the lower bound is ", round(low, 2), "%")
        print("Based on IQR, the upper bound is ", round(stock_info[i][4], 2), "% and the lower bound is ", round(stock_info[i][3], 2), "% \n")

def percentage_increase(stock_name, investment_period, historical_range):
    stock = yf.Ticker(stock_name)
    trading_days = round(investment_period*252/365) # converts real time into trading days
    hist = stock.history(period = historical_range, interval = "1d")
    data = hist[["Close"]]
    prev_price = data.shift(trading_days) # compares price to one (investment period) ago
    increase = data-prev_price # asks the question of "at this point in history, if I had held the stock for a year, what would be my return?"
    percentage_increase = increase/prev_price*100
    percentage_increase = percentage_increase.dropna()
    return(percentage_increase)
def lst_of_arr_to_lst_of_float(arr):   # converts a list of floats in numpy arrays to a list of floats
    ans=[]
    for i in range(len(arr)):
        ans.append(arr[i][0])
    return ans

def IQR_minimised(all_stocks, investment_period, historical_range):  # returns normalised ratios mased on maximising Q1 of the portfolio and respective Q1 and Q3 for that ratio
    ratios = []
    proportion = 1/len(all_stocks)
    IQRrisk = []
    stocklist = {}
    for i in range(len(all_stocks)):
        stocklist[i] = percentage_increase(all_stocks[i], investment_period, historical_range)
    for stock in range(len(all_stocks)):
        #print(stock)
        increase = stocklist[stock]["Close"]
        varQ1 = []
        #otherstocks = all_stocks.copy()
        #otherstocks.remove(otherstocks[stock])
        otherstocklist = stocklist.copy()
        del otherstocklist[stock]
        otherindexlist = list(range(len(all_stocks)))
        otherindexlist.remove(stock)
        # can change the minimum percent by changing the range of this for loop
        for r in range(99):
            ratio = (r+1)/100
            sharelost = proportion - ratio # max of 100 stocks to balance
            # share lost is to be distributed among the other stocks equally
            distribute = sharelost/(len(all_stocks)-1)
            otherratio = distribute + proportion
            y = ((increase.quantile(0.75)-increase.quantile(0.25))*ratio)**2
            #summedincrease = summedincrease.to_numpy()
            for i in otherindexlist:
                #print (i)
                y += (otherratio*(otherstocklist[i].quantile(0.75)-otherstocklist[i].quantile(0.25)))**2
                #inc = inc.to_numpy()
                #summedincrease[:][0] = summedincrease[:][0] + inc[:][0]
                #Q3 = np.quantile(summedincrease, 0.75)
                #Q1 = np.quantile(summedincrease, 0.25)
            y = y.to_numpy()
            varQ1.append((y**(1/2)))
            varQ = varQ1.copy()
            varQ = lst_of_arr_to_lst_of_float(varQ1)
        IQRrisk.append(varQ)
        del otherstocklist
    # why does IQR increase as the stock ratio increase? this causes a 1:1:1 ratio every time
    # can I treat the IQR as like the "uncertainty" and use the same error prop?
    # for each ratio y = ((IQR of stock A * ratio A)^2 + (IQR of stock B * ratio B)^2 + ...)**(1/2)
    for r in range(len(all_stocks)):
        minvalue = min(IQRrisk[r])
        index = IQRrisk[r].index(minvalue) + 1
        ratios.append(index)
    normratios = []
    for n in range(len(ratios)):
        normratios.append(round(ratios[n]/sum(ratios), 3))
    final_dist = 0
    for i in range(len(ratios)):
        final_dist += normratios[i]*stocklist[i]
    Q3 = final_dist.quantile(0.75)
    Q1 = final_dist.quantile(0.25)
    median = final_dist.median()
    mean = final_dist.mean()
    return(normratios, Q3["Close"], Q1["Close"], median["Close"], mean["Close"])
  
    
def SNP_compare(portfolio, SNP): # takes in the percentage gain from a given portfolio, compares it to the snp500 and gives a percent chance that you would have been better off buying the snp500
    win_counter = 0
    loss_counter = 0
    compare = portfolio - SNP
    for i in range(len(compare)):
        if compare["Close"][i] >= 0:
            win_counter += 1
        else:
            loss_counter += 1
    win_percent = (win_counter/(win_counter + loss_counter))*100
    return round(win_percent, 2)

def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))
        
def back_test(normratios, mean, median, SD, IQR, all_stocks, investment_period): # backtests a reccomendation over a period of 10 years
    #tickers = yf.Tickers(numstock)
    stockhist = {}
    for i in range(len(all_stocks)):
        stockhist[i] = percentage_increase(all_stocks[i], investment_period, "all")   # percent increase data to be backtested against
    # I want to backtest from 5 years in the past (ideally should depend on investment_period but wtv)
    import datetime as dt
    today = dt.datetime.today()
    today = today.replace(tzinfo=None)
    trading_days = stockhist[0].index
    last_trading_day = nearest(trading_days, today)
    
    ### DEVAX idk what to do here the datetime thing is insane
    return()
    

    
    
    
    
    
def main():
    numstock = input("Which stocks do you want to compare? \n")
    investment_period = input("What is your period of investment in days? \n")
    investment_period = float(investment_period)
    historical_range = input("What range of historical data do you want to consider? \n")
    #tickers = yf.Tickers(numstock)
    all_stocks = numstock.split()
    stock_info = []
    increase_dict = {}
    
    for i in range(len(all_stocks)):
        info = stock_eval(all_stocks[i], investment_period, historical_range)
        increase_dict[all_stocks[i]] = info[5]
        stock_info.append(info[0:5])
    # stock info contains a list of lists which each contain the mean, median, SD, q1, q3 of a stock
    increase_dict["SPY"] = percentage_increase("SPY", investment_period, historical_range)
    # print(increase_dict)
    if len(stock_info) == 1:
        print_info(all_stocks, investment_period, historical_range, stock_info)
        win_percent = SNP_compare(increase_dict[all_stocks[0]], increase_dict["SPY"])
        print("Buying this stock gives you a", win_percent, "% chance of beating the S&P500.\n")
        main()
        
    else:
        print_info(all_stocks, investment_period, historical_range, stock_info)
        SDprop = sdprop(stock_info) # calls the error propagation function for mean
        ratio = SDprop[0]
        SD = SDprop[1]
        
        meangain = 0
        summedincrease = 0
        for i in range(len(all_stocks)):
            increase = ratio[i]*(percentage_increase(all_stocks[i], investment_period, historical_range))
            #print(increase.head())
            summedincrease += increase
        median = summedincrease.median()["Close"]
        Q1 = summedincrease["Close"].quantile(0.25)
        Q3 = summedincrease["Close"].quantile(0.75)
        for i in range(len(all_stocks)):
            meangain += stock_info[i][0]*ratio[i]
        high = meangain + SD
        low = meangain - SD
        print("\nIf most of the stocks' distributions are symmetric, you should follow these measurements and buy according to this ratio:")  # important: mean and SD
        print("\n", all_stocks,"\n", ratio, "\n")
        print("This portfolio should yield a percentage gain of", round(meangain, 2), "% on average.")
        print("This portfolio should yield a median percentage gain of", round(median, 2), "%.")
        print("The upper bound according to error propagation is ", round(high, 2), "% and the lower bound is ", round(low, 2), "%.")
        print("Alternatively, you may judge the upper and lower bounds according to the IQR of the portfolio's percentage increases which are ", round(Q3, 2), "% and ", round(Q1, 2), "% respectively.")
        sym_portfolio = 0
        for i in range(len(all_stocks)):
            portion = ratio[i]*increase_dict[all_stocks[i]]
            sym_portfolio += portion
        win_percent = SNP_compare(sym_portfolio, increase_dict["SPY"])
        print("Buying in this ratio gives you a", win_percent, "% chance of beating the S&P500.\n")
        plt.hist(sym_portfolio["Close"], bins=30)
        plt.title('SD-based portfolio')
        plt.xlabel('Percentage Increase')
        plt.ylabel('Frequency')
        plt.show()
        
        
        #medhigh = median + 1.253*SD
        #medlow = median - 1.253*SD
        IQR_min = IQR_minimised(all_stocks, investment_period, historical_range)
        IQRratio = IQR_min[0]
        Q3IQR = IQR_min[1]
        Q1IQR = IQR_min[2]
        print("\nIf most of the stocks' distributions are skewed, you should follow the median and IQR measurements and buy according to this ratio:")
        print("\n", all_stocks,"\n", IQRratio, "\n")
        print("This portfolio should yield a percentage gain of", round(IQR_min[4], 2), "% on average.")
        print("This portfolio should yield a median percentage gain of", round(IQR_min[3], 2), "%.")
        print("The upper bound according to error propagation is ", round(Q3IQR, 2), "% and the lower bound is ", round(Q1IQR, 2), "%.")
        #print("Alternatively, you may judge the upper and lower according to the IQR of the portfolio's percentage increases which are ", round(Q3, 2), "% and ", round(Q1, 2), "% respectively. \n")
        asym_portfolio = 0
        for i in range(len(all_stocks)):
            portion = IQRratio[i]*increase_dict[all_stocks[i]]
            asym_portfolio += portion
        IQRwin_percent = SNP_compare(asym_portfolio, increase_dict["SPY"])
        print("Buying in this ratio gives you a", IQRwin_percent, "% chance of beating the S&P500.\n")
        plt.hist(asym_portfolio["Close"], bins=30)
        plt.title('Median-based portfolio')
        plt.xlabel('Percentage Increase')
        plt.ylabel('Frequency')
        plt.show()
        #print(median)
        main()

    
        

    #plt.plot(sdrisk[0])  ## i need another way of defining risk cuz now it just suggests to put all your money in the stock with the lowest max potential loss
   # print(stock_info)
print("Key assumptions of this tool: \n1. Price of stock A is independent from price of stock B. \n2. Price changes of a stock are assumed to be independent from other price changes of that same stock. \n3. The investor is always going long and holding for the specified investment term. \n")
main()
