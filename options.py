import QuantLib as ql
from py_vollib.black_scholes import black_scholes
from py_vollib.black_scholes import implied_volatility
import yfinance as yf
import pandas as pd


def find_option_contract(symbol, predicted_price, expiry_days, max_price, option_type):
    # Fetch option chain
    option_chain = yf.Ticker(symbol).option_chain()

    # Filter option chain based on expiry date, option type, and maximum price
    options = option_chain.calls if option_type == 'call' else option_chain.puts

    #options = options[options['expirationDate'] == expiry_days]
    options = options[options['lastPrice'] <= max_price]

    # Find the closest match for the strike price
    closest_strike = options['strike'].iloc[(options['strike'] - predicted_price).abs().idxmin()]
    
    # Filter options based on the closest strike price
    closest_option = options[options['strike'] == closest_strike]

    return closest_option


# Example usage
# symbol = "SPY"
# predicted_price = 410.0
# expiry_days = 30
# max_price = 5.0
# option_type = 'call'

# closest_option = find_option_contract(symbol, predicted_price, expiry_days, max_price, option_type)
# print(closest_option)


def get_risk_free_rate():

    calendar = ql.NullCalendar()
    today = ql.Date().todaysDate()
    settlement_date = ql.TARGET().advance(today, 2, ql.Days)
    tenor = ql.Period(1, ql.Years)
    rate_helpers = [ql.DepositRateHelper(ql.QuoteHandle(ql.SimpleQuote(0.0)), tenor, 0, calendar,
                                         ql.ModifiedFollowing, False, ql.Actual360())]
    yield_curve = ql.PiecewiseLogCubicDiscount(settlement_date, rate_helpers, ql.Actual365Fixed())
    yield_curve.enableExtrapolation()
    risk_free_rate = yield_curve.zeroRate(tenor, ql.Compounded, ql.Annual).rate()

    return risk_free_rate

def get_volatility(option_type, underlying_price, strike_price, option_price, risk_free_rate):

    py_vollib_volatility = implied_volatility(option_price, underlying_price, strike_price, risk_free_rate, 30, option_type.lower())
    return py_vollib_volatility

def calculate_option_price(option_type, underlying_price, strike_price, expiration_date, dividend_yield):

    today = ql.Date().todaysDate()
    ql.Settings.instance().evaluationDate = today

    ql_option_type = ql.Option.Put if option_type == 'put' else ql.Option.Call
    payoff = ql.PlainVanillaPayoff(ql_option_type, strike_price)
    exercise = ql.AmericanExercise(today, expiration_date)
    ql_option = ql.VanillaOption(payoff, exercise)


    risk_free_rate = get_risk_free_rate()
    spot_handle = ql.QuoteHandle(ql.SimpleQuote(underlying_price))
    flat_ts = ql.YieldTermStructureHandle(ql.FlatForward(today, risk_free_rate, ql.Actual365Fixed()))
    dividend_ts = ql.YieldTermStructureHandle(ql.FlatForward(today, dividend_yield, ql.Actual365Fixed()))

    
    implied_vol = get_volatility(option_type, underlying_price, strike_price, option_price, risk_free_rate)

    vol_ts = ql.BlackConstantVol(today, ql.NullCalendar(), implied_vol, ql.Actual365Fixed())
    process = ql.BlackScholesMertonProcess(spot_handle, dividend_ts, flat_ts, vol_ts)
    engine = ql.BaroneAdesiWhaleyEngine(process)
    ql_option.setPricingEngine(engine)
    option_price = ql_option.NPV()

    return option_price


# # Example usage
# option_type = 'put'  
# underlying_price = 300 
# strike_price = 290  
# expiration_date = ql.Date(31, 12, 2023)  # Option expiration date
# dividend_yield = 0.0  # Dividend yield of the underlying asset
# option_price = 15.0  # Market price of the option
# risk_free_rate = get_risk_free_rate()
# implied_volatility = get_volatility(option_type, underlying_price, strike_price, option_price, risk_free_rate)



#######################################################################################################################
# We first use the calculate_option_price to compare the market price to the theoretical price of the option contract
# then we need to predict the underlying stock price -> then we can use the calculate_option_price again to see what the potential profits are