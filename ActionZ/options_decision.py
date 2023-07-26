import options
from simple_stats_strike import get_1wk_dte_option_details


def undervalued(actual_price, theoretical_price):
    return theoretical_price > actual_price

def scam(actual_price, theoretical_price, threshold = -1):
    return (theoretical_price-actual_price) < threshold

def options_decision(symbol, scamcheck = True, undervaluecheck = False):
    options_info = get_1wk_dte_option_details(symbol)
    expiry_days = 7
    if options_info is None:
        print('No good trades for now, try again later!')
        return None
    option_type, strike_price = options_info
    wanted_option = options.find_option_contract(symbol, strike_price, expiry_days, max_price=50, option_type=option_type)
    theoretical_price = options.worth_or_not(symbol, wanted_option['strike'], wanted_option['impliedVolatility'], expiry_days, option_type)['Option Price']
    actual_price = wanted_option['lastprice'].iloc[0]
    # option 1: determine if the option is 'undervalued' by the market
    # option 2: just don't get scamemd, simply check if the pricing of the option is close enough
    if scamcheck and scam(actual_price, theoretical_price):
        print('Watch out! this option might be a scam!')
        return None
    
    if undervaluecheck:
        if undervalued(actual_price, theoretical_price):
            print('This option is probably a good buy!')
            return wanted_option['contractSymbol'].iloc[0]
        
        elif not undervalued(actual_price, theoretical_price):
            print('This option is relatively expensive, try a different one!')
            return None
    
    return wanted_option['contractSymbol'].iloc[0]