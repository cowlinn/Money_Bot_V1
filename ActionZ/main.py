from actions import *
from weights_optimisation import *

ib = IB() #initialize main instance 

##TODO: check if we need to regenerate any persistent data here?


##main functions triggers the process of the app 
##the behaviour descibed is as follows 


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
def once_every_day():
    run_optimization()


## start of day: connect bot
def start_of_day():
    connection_setup(ib)

    pass

## end of day: disconnect bot 
## end all trades
def end_of_day():
    connection_teardown(ib)


#main seq of events
def main():
    
    check_prev_positions(ib)

    ##TODO: we dun have subscription yet / not trading hours
    prev_data = req_prev_data(ib)


    ##





#once every 15 minutes
main()



