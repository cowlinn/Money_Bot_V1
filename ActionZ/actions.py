import threading
import time
from ib_insync import *

#from weights_optimisation import *
import yfinance as yf
import underlyingTA



ib = IB() #instance of ibkr 

def connection_setup(my_ib):
    api_thread = threading.Thread(target=actual_connection(my_ib), daemon=True)
    api_thread.start()
    my_ib.sleep(1)
    
##take in an instance of ibkr and perform login, assuming instance of IBGateway is running
##in the background
def actual_connection(my_ib, localhost='127.0.0.1', connection_port=7497):
    my_ib.connect()
    #my_ib.connect(localhost, connection_port, clientId=123)
    print("IBKR SUCC CONNECTED")



def connection_teardown(my_ib):
    my_ib.disconnect() #disconnects the current ib_sync instance
    print("HL SAYS BYEBYE")
#by default, we can req prev data
spy_monitor = Stock('SPY', 'SMRT', 'USD') #ticker object to find stonks we are int in


##based on the stocks we are currently monitoring, display the result inside a Pandas DF

##TODO: do we want more combination for this?
##ok it doesn't work cuz it's not working
def req_prev_data(ib, duration_str='30 D'):
    bars = ib.reqHistoricalData(
    spy_monitor, endDateTime='', durationStr=duration_str,
    barSizeSetting='1 hour', whatToShow='MIDPOINT', useRTH=True)

    # convert to pandas dataframe
    df = util.df(bars)
    return df



##TODO: check what the format of this looks like, and sell stuff that we should
def check_prev_positions(ib):
    prev = ib.positions() #a list of positions we are holdin
    open_trades = ib.openTrades() #this shld be all closed?

    print(prev)
    print(open_trades)


    if not prev:
        return
    
    for pos in prev:

        ##DO SOMETHING
        pass


connection_setup(ib)
print(req_prev_data(ib))
print(check_prev_positions(ib))
connection_teardown(ib)




##WARNING, THIS IS A SUPER COSTLY OPERATION
##ONLY DO IT TO UPDATE THE TRAINING WEIGHTS ONCE EVERY
## X AMOUNT OF TIME!

data_period = "4d"
resolution = "15m"
def run_optimization(current_stocks = ['SPY']):
    for i in current_stocks:
        print(i + " check")
        underlyingTA.optimise_decision(i) # it will just write a bunch of log files


trades = run_optimization()

print(trades)