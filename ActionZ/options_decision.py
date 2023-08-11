import options
from simple_stats_strike import get_1wk_dte_option_details
import pytz
from datetime import datetime, timedelta


def undervalued(actual_price, theoretical_price):
    return theoretical_price > actual_price

def scam(actual_price, theoretical_price, threshold = -0.5):
    return (theoretical_price-actual_price) < threshold

def options_decision(symbol, scamcheck = True, scam_threshold = -1.2, undervaluecheck = False, date = 'normal options date'):
    options_info = get_1wk_dte_option_details(symbol)
    expiry_days = 7
    formatted_expiry_date = options.get_expiry_date(expiry_days).strftime("%y%m%d")
    if date == 'menal ibkr date':
        formatted_expiry_date = '20'+formatted_expiry_date
    if options_info is None:
        print('No good trades for now, try again later!')
        return None
    option_type, strike_price = options_info
    if option_type == 'call':
        otype = 'C'
    else:
        otype = 'P'
    wanted_option = options.find_option_contract(symbol, strike_price, expiry_days, max_price=50, option_type=option_type)
    if wanted_option is None:
        print('No closest contract available, try another date or a different ticker symbol!')
        return
    theoretical_price = options.why_go_through_trouble(symbol, int(wanted_option['strike'].iloc[0]), wanted_option['impliedVolatility'].iloc[0], expiry_days, option_type)
    actual_price = wanted_option['lastPrice'].iloc[0]
    return_tuple = (symbol, formatted_expiry_date, int(wanted_option['strike'].iloc[0]), otype, 'SMART')

    # option 1: determine if the option is 'undervalued' by the market
    # option 2: just don't get scamemd, simply check if the pricing of the option is close enough
    if scamcheck and scam(actual_price, theoretical_price):
        print('Watch out! This option might be a scam!')
        return None
    if not options.liquidity_check(symbol, option_type, expiry_days): # always check liquidity to avoid losing to bid-ask spread
        print('Not enough liquidity!')
        return None
    if undervaluecheck:
        if undervalued(actual_price, theoretical_price, threshold = scam_threshold):
            print('This option is probably a good buy!')
            # return wanted_option['contractSymbol'].iloc[0]
            return return_tuple
        
        elif not undervalued(actual_price, theoretical_price):
            print('This option is relatively expensive, try a different one!')
            return None
    
    # return wanted_option['contractSymbol'].iloc[0]
    return return_tuple

# TODO: log options trades in db

def close_position(symbol:str, profit_threshold = 1.3, max_hold_days = 3):
    """
    checks if the wanted contract is sellable
    
    symbol:str is the ticker symbol
    max_hold_days:int is the hard limit on how many days we hold a contract
    profit_threshold:float is the desired profit level
    
    returns a list of GUIDs for option contracts to sell
    """
    # assume that option trades are logged in db, with GUID {symbol}{expiry_date}{strike_price}
    # the table will contain {symbol}    {option_type}    {actual_buying_price}    {date_of_purchase}

    # first, read the db by {symbol} to see if any options for a given ticker have profit of 30%
    
    # add all the GUID for a given symbol to a list
    guid_list = []
    sell_list = []
    # iterate through the list and look up the current price for each option and see if the option meets the profit threshold
    symlen = len(symbol)
    us_timezone = pytz.timezone('America/New_York')
    us_time =  datetime.now(us_timezone)
    for i in guid_list:
        expiry_date_str = i[symlen:(symlen+10)]
        exp_date = datetime(int(expiry_date_str[:4]), int(expiry_date_str[5:7]), int(expiry_date_str[8:]), 12, 0, 0, 0, us_timezone)
        strike_price = i[symlen+10:] # do we even need this
        date_of_purchase = 0 # PLACEHOLDER, store the datetime obj in sqlite db and read directly
        actual_buying_price = 0 # PLACEHOLDER, TODO
        option_type = 'call' # PLACEHOLDER, ALSO NEED TO READ FROM DB
        
        days_held = int(str(us_time - date_of_purchase).split()[0]) # might not work properly
        current_days_to_expiry = int(str(exp_date - us_time).split()[0])
        current_price = options.find_option_contract(symbol, strike_price, current_days_to_expiry, 50, option_type)['lastPrice'].iloc[0]
        
        # first we check if it's too close to expiring
        if days_held <= max_hold_days:
            sell_list.append(i)
        # then we check if the profit target is met
        elif current_price/actual_buying_price > profit_threshold:
            sell_list.append(i)
    # ID = symbol + str(expiry_date) + str(strike_price)
    return sell_list
    