import options
from simple_stats_strike import get_1wk_dte_option_details


def undervalued(actual_price, theoretical_price):
    return theoretical_price > actual_price

def scam(actual_price, theoretical_price, threshold = -1):
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
    theoretical_price = options.why_go_through_trouble(symbol, int(wanted_option['strike'].iloc[0]), wanted_option['impliedVolatility'].iloc[0], expiry_days, option_type)
    actual_price = wanted_option['lastPrice'].iloc[0]
    return_tuple = (symbol, formatted_expiry_date, int(wanted_option['strike'].iloc[0]), otype, 'SMART')

    # option 1: determine if the option is 'undervalued' by the market
    # option 2: just don't get scamemd, simply check if the pricing of the option is close enough
    if scamcheck and scam(actual_price, theoretical_price):
        print('Watch out! this option might be a scam!')
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
