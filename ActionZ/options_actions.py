##a cleaner version of actions, only required for options

from ib_insync import * 
from options_decision import options_decision
from telegram import send_tele_message



def run_option_trades(my_ib, day_actions:dict, current_stocks= ['SPY', 'TSLA']):
    """
    this function is the main entry point into the prog \n 
    runs through the list of current stocks
    """
    for ticker_name in current_stocks:
        make_option_trade(my_ib,ticker_name)


def make_option_trade(my_ib:IB, ticker):
    """
    for each ticker, use `options_decision` to make a trade \n 
    """
    ### very barebones make_trade
    x = options_decision(ticker)
    if x is None:
        return
    
    ##else, we continue doing!
    options_contract = create_options_contract(my_ib,ticker)
    my_ib.qualifyContracts(options_contract)
    assert (options_contract != None)

    ##create a generic order
    options_order = create_options_order(my_ib=my_ib)

    trade = my_ib.placeOrder(options_contract, options_order)
     ##TODO: log the trade within a dictionary
    my_ib.sleep(5)
    
    order_status = my_ib.trades()[-1].orderStatus 
    send_tele_message(f"Order status: {order_status.status} for {ticker}")

   


def create_options_contract(my_ib:IB,ticker_name:str):
    """
    Creates a barebones options contract, returns none if doesn't exist 
    """
    x = options_decision(ticker_name)
    if x is not None:
        ticker,expiry, price, decision, routing = options_decision(ticker_name, date='menal ibkr date')
        current_funds = get_liquid_funds(my_ib)
        if current_funds > (price *2): ##arbitrary threshold to buy
            send_tele_message(f"making an options_trade where ticker = {ticker}, expiry = {expiry}, price = {price}, decision  = {decision}, routing = {routing}")
            return Option(ticker, expiry, price, decision, routing) #hope for the best prayge
    return None 


##TODO: check if we still really need to pass ib as an argument
def create_options_order(my_ib:IB, action='BUY'):
    """
    Creates a simple marketOrder (2 stocks) \n
    Anyways, we can't short yet
    """
    ## switched to options 
    my_order = MarketOrder(action, 2)

    #need to auto transmit
    my_order.transmit = True
    return my_order



def get_liquid_funds(my_ib:IB):
    '''
    Given an account, return the funds as a float \n
    Just to check if we can buy the opt in the first place
    '''
    ##get summary from our only account
    accounts = my_ib.managedAccounts()
    account = accounts[0]  # Assuming you have only one account

    # Retrieve the account information
    account_data = my_ib.accountSummary(account=account)

    ##loop through and get the account data 

    liquid_funds = next((item for item in account_data if item.tag == 'AvailableFunds'), None)
    return float(liquid_funds.value)