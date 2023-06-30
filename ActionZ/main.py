from actions import *
from weights_optimisation import *
from ib_insync import * 



ib = IB() #initialize main instance 

##TODO: check if we need to regenerate any persistent data here?


##main functions triggers the process of the app 
##the behaviour descibed is as follows 

##THIS IS OUR SINGLE SOURCE OF TRUTH 
##ON WHATEVER STOCKS WE ARE MONITORING

current_stocks_to_monitor =  ['SPY', 'TSLA', 'NVDA', 'V', 'MA', 'AMD', 'PYPL', 'GME', 'PLTR', 
                                'MSFT', 'GOOGL', 'JPM', 'DIS', 'NFLX', 'MMM', 'CAT', 'NKE', 
                                'WMT','COST', 'CSCO', 'PFE', 'SSL', 'RIOT', 'GILD', 'AMZN', 'BABA']












## Check market open or not
## Check positions, funds - Make sure nothing we don't want is there - Check number of day trades
## Get Market data for stock price (SPY)
## Do TA on underlying to get predicted direction and price.
## Get Option chain data. Use predicted price to filter for suitably priced options (call/put) - Take w/ a grain of salt
## For the above, we need to see whether the option is overpriced or not, and filter using our funds 
## Then we calculate the option contract price when it goes our way to determine a suitable price to sell (Exit strategy)
## Set a stop loss as well
## Note that we may not make trades some days, if it doesn't pass our condition (This is the part where we need to constantly improve on)
## If we do make a trade, record it down and send a telegram message


#actions we run not as requently
##optimization basically fetches a bunch of "Weights" 
##for the day, that we will query based on
def once_every_day():
    #check_prev_positions(ib)
    #run_optimization(current_stocks=current_stocks_to_monitor)
    pass
    


## start of day: connect bot
def start_of_day(my_ib):
    connection_setup(my_ib)
    once_every_day()

## end of day: disconnect bot 
## end all trades
def end_of_day(my_ib):
    connection_teardown(my_ib)


#main seq of events
def main(my_ib):


    ##TODO: for the actual options bot, we need to manually check Theta
    ##ad sell our open options based on theta
    check_prev_positions(my_ib)

    ##TODO: we dun have subscription yet / not trading hours 
    ##So we cannot find previous data 
    prev_data = req_prev_data(my_ib)

    #current_stocks_to_monitor = underlyingTA.cleanup(current_stocks_to_monitor)


    run_trades(my_ib, current_stocks=current_stocks_to_monitor)



###start of day ##

start_of_day(ib)

#once every 15 minutes, total of 5 hours (20 intervals)
counter = 0
while counter <= 20:
    main(ib)
    time.sleep(900)
    counter +=1 

###end of day 

end_of_day(ib)
