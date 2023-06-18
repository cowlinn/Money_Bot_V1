import threading
import time
from ib_insync import *

#from weights_optimisation import *
import yfinance as yf
from underlyingTA import*


ib = IB() #instance of ibkr 


##take in an instance of ibkr and perform login, assuming instance of IBGateway is running
##in the background
def connection_setup(ib, localhost='127.0.0.1', connection_port=7497):
    ib.connect(localhost, connection_port, clientId=123)
    print("CONNECTED")

stock = Stock('SPY', 'TSLA') #ticker object to find stonks we are int in


##based on the stocks we are currently monitoring, display the result inside a Pandas DF

##TODO: do we want more combination for this?
def req_prev_data(ib, duration_str='30 D'):
    bars = ib.reqHistoricalData(
    stock, endDateTime='', durationStr=duration_str,
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

api_thread = threading.Thread(target=connection_setup, daemon=True)
api_thread.start()
time.sleep(1)

print(req_prev_data)
print(check_prev_positions(ib))




##WARNING, THIS IS A SUPER COSTLY OPERATION
##ONLY DO IT TO UPDATE THE TRAINING WEIGHTS ONCE EVERY
## X AMOUNT OF TIME!

data_period = "4d"
resolution = "15m"
def run_optimization(current_stocks = ['SPY', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'GOOGL', 'NVDA', 'MA', 'V']):
    for i in current_stocks:
        optimise_decision(i) # it will just write a bunch of log files


#run_optimization()

