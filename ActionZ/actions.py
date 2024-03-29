from datetime import datetime
import threading
import time
from ib_insync import *

#from weights_optimisation import *
import yfinance as yf
import underlyingTA
import options
from telegram import send_tele_message





def connection_setup(my_ib):
    actual_connection(my_ib)
    my_ib.sleep(1)
    
##take in an instance of ibkr and perform login, assuming instance of IBGateway is running
##in the background
def actual_connection(my_ib, localhost='127.0.0.1', connection_port=7497):
    my_ib.connect(host=localhost, port=connection_port, clientId=125)
    #my_ib.connect(localhost, connection_port, clientId=123)
    print("IBKR SUCC CONNECTED")



def connection_teardown(my_ib):
    my_ib.disconnect() #disconnects the current ib_sync instance
    print("HL SAYS BYEBYE")
#by default, we can req prev data
spy_monitor = Stock('SPY', 'SMART', 'USD') #ticker object to find stonks we are int in


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
        res += (f"{i}: {lst[i]}" + '\n')
    send_tele_message(res)
##TODO: check what the format of this looks like, and sell stuff that we should


def check_prev_positions(my_ib:IB, day_actions:dict):
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

    
    msg = ""
    for trade in day_actions:
        trade_msg = f"currently looking at the history for {trade} \n"

        ##we assume at this point, log_entry[trade_key] = Trade object
        for log_entry in day_actions[trade].log:
            trade_msg += f"{log_entry} \n"
        

        trade_msg += "history of {trade} completed \n"

        msg += trade_msg
    send_tele_message(msg)






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


def make_trade(trade_dict, action, ticker, my_ib: IB, trade_actions:dict):
    if not trade_dict:
        return 
    for date in trade_dict:
        purchase_price, stoploss, take_profit = trade_dict[date]
        current_funds = get_liquid_funds(my_ib)

        if current_funds > purchase_price: #shld be purchase * quantity tbh
            #make the trade?
            #step 1: create the contract
            contract = create_contract(ticker_name=ticker)
            my_ib.qualifyContracts(contract)

            #step 2: create the order 
            #TODO: check if buy or sell?
            bracket_order = create_order(my_ib,purchase_price, stoploss, take_profit, order_size=1, action=action)        
            
            send_tele_message(f"should be doing a {action} for {ticker} with price {purchase_price}, stoploss: {stoploss}, take_profit: {take_profit}")
            #bracket_order = my_ib.bracketOrder(action, 20, purchase_price, take_profit, stoploss)
            #make the trade
            is_parent_trade = True
            for o in bracket_order:

                trade = my_ib.placeOrder(contract, o)
                my_ib.sleep(5) #general wait to gather
                if is_parent_trade:
                    while not trade.isDone():
                        my_ib.waitOnUpdate()
                    is_parent_trade = False #only wait for the parent to go in 

                #trade = ib.placeOrder(contract, bracket_order)
                #my_ib.sleep(25)  # Sleep for a moment to allow trade executio
                # Check the order status of the most recent one? (including parents?)
                order_status = my_ib.trades()[-1].orderStatus 
                print(f"Order status: {order_status.status} for {ticker} with action {action}")
                send_tele_message(f"Order status: {order_status.status} for {ticker} with action {action}")

                trade_key = ticker + " " + str(datetime.now)
                
                ##register the current order object inside the dictionary
                trade_actions[trade_key] = trade



# def make_option_trade(trade_dict, action, ticker, my_ib: IB, trade_actions:dict):
#     if not trade_dict:
#         return 
#     for date in trade_dict:
#         ## These prices will be the contract prices
#         predicted_price, stoploss, take_profit = trade_dict[date]
#         current_funds = get_liquid_funds(my_ib)

#         current_price = 
#         current_contract = options.find_option_contract(ticker, current_price, )
#         best_contract = options.find_option_contract(ticker, predicted_price, 5, 10, "call")

#         if not (options.liquidity_check(ticker, "call")):
#             return
        
#         check_contract = options.worth_or_not(ticker,best_contract['strike'],best_contract['impliedVolatility'],
#                                               5,'call')
        
#         if not check_contract['Option Price'] == best_contract['lastPrice']:
#             return

#         if current_funds > ( * 100): 
#             #make the trade?
#             #step 1: create the contract
#             contract = create_option_contract(ticker_name=ticker)
#             my_ib.qualifyContracts(contract)

#             #step 2: create the order 
#             #TODO: check if buy or sell? -- For options we can't sell unless margin
#             bracket_order = create_order(my_ib,purchase_price, stoploss, take_profit, order_size=1, action="BUY")        
            
#             send_tele_message(f"should be doing a {action} for {ticker} with price {purchase_price}, stoploss: {stoploss}, take_profit: {take_profit}")
#             #bracket_order = my_ib.bracketOrder(action, 20, purchase_price, take_profit, stoploss)
#             #make the trade
#             is_parent_trade = True
#             for o in bracket_order:

#                 trade = my_ib.placeOrder(contract, o)
#                 my_ib.sleep(5) #general wait to gather
#                 if is_parent_trade:
#                     while not trade.isDone():
#                         my_ib.waitOnUpdate()
#                     is_parent_trade = False #only wait for the parent to go in 

#                 #trade = ib.placeOrder(contract, bracket_order)
#                 #my_ib.sleep(25)  # Sleep for a moment to allow trade executio
#                 # Check the order status of the most recent one? (including parents?)
#                 order_status = my_ib.trades()[-1].orderStatus 
#                 print(f"Order status: {order_status.status} for {ticker} with action {action}")
#                 send_tele_message(f"Order status: {order_status.status} for {ticker} with action {action}")

#                 trade_key = ticker + " " + str(datetime.now)
                
#                 ##register the current order object inside the dictionary
#                 trade_actions[trade_key] = trade

def run_trades(my_ib, day_actions:dict, current_stocks= ['SPY', 'TSLA'] ):
    for ticker_name in current_stocks:
        print(f"checking to see if there are good trades for {ticker_name}")
        send_tele_message(f"checking to see if there are good trades for {ticker_name}")
        decision = underlyingTA.decision(ticker_name) # it will just write a bunch of log files


        ##TODO: check if we are alr holding a stock in current_stocks, if we are then fk it 

        ##LOGIC TO EXECUTE TRADE
        #this "trade" key is a datetime obj
        call_dict, put_dict = decision

        make_trade(call_dict, 'BUY', ticker_name, my_ib, day_actions)
        make_trade(put_dict, 'SELL', ticker_name, my_ib, day_actions)

def run_option_trades(my_ib, day_actions:dict, current_stocks= ['SPY', 'TSLA'] ):
    for ticker_name in current_stocks:
        print(f"checking to see if there are good trades for {ticker_name}")
        send_tele_message(f"checking to see if there are good trades for {ticker_name}")
        decision = underlyingTA.decision(ticker_name) # it will just write a bunch of log files


        ##TODO: check if we are alr holding a stock in current_stocks, if we are then fk it 

        ##LOGIC TO EXECUTE TRADE
        #this "trade" key is a datetime obj
        call_dict, put_dict = decision


        make_option_trade(call_dict, 'BUY', ticker_name, my_ib, day_actions)
        make_option_trade(put_dict, 'SELL', ticker_name, my_ib, day_actions)


def create_contract(ticker_name):
    contract = Contract()
    contract.symbol = ticker_name  # Symbol of the stock
    contract.secType = 'STK'  # Security type: 'STK' for stock
    contract.exchange = 'SMART'  # Exchange: 'SMART' for SmartRouting
    contract.currency = 'USD'  # Currency

    ##manually create a stonk, but we can use contract ig?
    contract_stock = Stock(ticker_name,'SMART', 'USD')
    return contract_stock

def create_option_contract(ticker_name):
    contract = Contract()
    contract.symbol = ticker_name  # Symbol of the stock
    contract.secType = 'OPT'  
    contract.exchange = 'SMART'  # Exchange: 'SMART' for SmartRouting
    contract.currency = 'USD'  # Currency

    ##manually create an option, but we can use contract ig?
    #contract_option = Option(ticker_name,'SMART', 'USD')
    return contract


##TODO: check how to create order to buy (or short sell?)
## we buy one stock?
def create_order(my_ib:IB , purchase_price, stoploss, take_profit, order_size=100, action='BUY'):
    # Define the parent order
    # parent_order = Order(
    #     action=action,  # 'BUY' or 'SELL'
    #     totalQuantity=order_size,  # Total quantity of the asset
    #     orderType='MKT',  # Order type: 'LMT' for limit order
    #     lmtPrice=purchase_price  # Limit price
    # )

    # # Define the stop-loss order
    # stop_loss_order = Order(
    #     action='SELL'if action=='BUY' else 'BUY',  # Opposite action of the parent order
    #     totalQuantity=order_size,
    #     orderType='STP',  # Order type: 'STP' for stop order
    #     auxPrice=stoploss  # Stop price
    # )

    # # Define the take-profit order
    # take_profit_order = Order(
    #     action='SELL'if action=='BUY' else 'BUY',  # Opposite action of the parent order
    #     totalQuantity=order_size,
    #     orderType='LMT',  # Order type: 'LMT' for limit order
    #     lmtPrice=take_profit # Limit price
    # )
    
    bracket_order = my_ib.bracketOrder(action, 1, purchase_price, take_profit, stoploss)
    bracket_order.parent.orderType = 'MKT'
    bracket_order.parent.transmit = True
    return bracket_order


