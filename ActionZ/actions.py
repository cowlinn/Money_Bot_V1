from datetime import datetime
import threading
import time
from ib_insync import *

#from weights_optimisation import *
import yfinance as yf
import underlyingTA

from telegram import send_tele_message



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
def req_prev_data(my_ib, duration_str='30 D'):
    bars = my_ib.reqHistoricalData(
    spy_monitor, endDateTime='', durationStr=duration_str,
    barSizeSetting='1 hour', whatToShow='MIDPOINT', useRTH=True)

    # convert to pandas dataframe
    df = util.df(bars)
    return df


#turns list into nice helper list
def helper_list_print(message, lst):
    res = message + '\n'
    for i in range(len(lst)):
        res += (f"{i}: {lst[i]}" + '/n')
    send_tele_message(res)
##TODO: check what the format of this looks like, and sell stuff that we should


def check_prev_positions(my_ib):
    prev_positions = my_ib.positions() #a list of positions we are holdin
    open_trades = my_ib.openTrades() #this shld be all closed?

    helper_list_print("Here's a list of our prev_positions: ", prev_positions)
    helper_list_print("Here's a list of our open_trades: ", open_trades)

    funds = get_liquid_funds(my_ib)
    send_tele_message(f"By the way, you have $USD {funds} left")

    for pos in prev_positions:
        pass
    
    for pos in open_trades:

        ##DO SOMETHING
        pass






##WARNING, THIS IS A SUPER COSTLY OPERATION
##ONLY DO IT TO UPDATE THE TRAINING WEIGHTS ONCE EVERY
## X AMOUNT OF TIME!

data_period = "4d"
resolution = "15m"

## for current stocks, we only have the following 2 to optimise decision from
def run_optimization(current_stocks = ['SPY', 'TSLA']):
    for i in current_stocks:
        print(i + " doing optimize on " + str(datetime.now()))
        underlyingTA.optimise_decision(stock_name=i) # it will just write a bunch of log files




##returns liquid funds from ib_insyc
def get_liquid_funds(my_ib):
    ##get summary from our only account
    accounts = my_ib.managedAccounts()
    account = accounts[0]  # Assuming you have only one account

    # Retrieve the account information
    account_data = my_ib.accountSummary(account=account)

    ##loop through and get the account data 

    liquid_funds = next((item for item in account_data if item.tag == 'AvailableFunds'), None)
    return float(liquid_funds.value)



def run_trades(my_ib, current_stocks= ['SPY', 'TSLA']):
    for ticker_name in current_stocks:
        print(f"checking to see if there are good trades for {ticker_name}")
        decision = underlyingTA.decision(ticker_name) # it will just write a bunch of log files


        ##TODO: check if we are alr holding a stock in current_stocks, if we are then fk it 

        ##LOGIC TO EXECUTE TRADE
        #this "trade" key is a datetime obj
        for trade in decision:

            if not trade:
                send_tele_message(f"no trades for {ticker_name}")
                break


            print("printing trades")
            for date in trade:
                purchase_price, stoploss, take_profit = trade[date]
                 ##check funds 
                current_funds = get_liquid_funds(my_ib)
                print(f"purchase_price={purchase_price}, stoploss = {stoploss}, take_proft = {take_profit}")
                print(f"current_funds = {current_funds}")
                if current_funds > purchase_price:
                    #make the actual trade using the stoploss and tp
                    
                    #step 1: create the contract
                    contract = create_contract(ticker_name=ticker_name)


                    #step 2: create the order 
                    #TODO: check if buy or sell?
                    bracket_order = create_order(purchase_price, stoploss, take_profit)

                    #make the trade
                    for o in bracket_order:
                        ib.placeOrder(contract, o)
                        
                    #trade = ib.placeOrder(contract, bracket_order)
                    ib.sleep(1)  # Sleep for a moment to allow trade executio
                    # Check the order status
                    order_status = ib.trades()[trade].orderStatus


                    ##HERE: send a tele message xd 
                    print("Order status:", order_status.status)
                    send_tele_message("Order status:", order_status.status)

def create_contract(ticker_name):
    contract = Contract()
    contract.symbol = ticker_name  # Symbol of the stock
    contract.secType = 'STK'  # Security type: 'STK' for stock
    contract.exchange = 'SMART'  # Exchange: 'SMART' for SmartRouting
    contract.currency = 'USD'  # Currency
    return contract



##TODO: check how to create order to buy (or short sell?)
def create_order(purchase_price, stoploss, take_profit, order_size=30, action='BUY'):
    # Define the parent order
    parent_order = Order(
        action=action,  # 'BUY' or 'SELL'
        totalQuantity=order_size,  # Total quantity of the asset
        orderType='LMT',  # Order type: 'LMT' for limit order
        lmtPrice=purchase_price  # Limit price
    )

    # Define the stop-loss order
    stop_loss_order = Order(
        action='SELL'if action=='BUY' else 'BUY',  # Opposite action of the parent order
        totalQuantity=order_size,
        orderType='STP',  # Order type: 'STP' for stop order
        auxPrice=stoploss  # Stop price
    )

    # Define the take-profit order
    take_profit_order = Order(
        action='SELL'if action=='BUY' else 'BUY',  # Opposite action of the parent order
        totalQuantity=order_size,
        orderType='LMT',  # Order type: 'LMT' for limit order
        lmtPrice=take_profit # Limit price
    )

    bracket_order = BracketOrder(parent=parent_order, stopLoss=stop_loss_order, takeProfit=take_profit_order)
    return bracket_order
