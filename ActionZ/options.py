import QuantLib as ql
from py_vollib.black_scholes import black_scholes
from py_vollib.black_scholes import implied_volatility
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import requests


## Long call, Long Put, Long Straddle, Long Strangle 
## Have something to indicate earnings season
## Have something to indicate whether we are bullihs/bearish/neutral


# We need to come up with something that determine the number of days to expiry (Need to be fixed)
# Need to also have something that sees what our max_price would be (max_price refers to the price of CONTRACT)
# Take note, last price would need to x100
# For predicted_price, we would probably need to hike it up abit cause if too close to our strike, very expensive (unless expiry low BUT like that v risky)

def find_option_contract(symbol, predicted_price, expiry_days, max_price, option_type):
    us_timezone = pytz.timezone('America/New_York')
    us_time =  datetime.now(us_timezone)
    formatted_date = us_time.strftime("%y%m%d")
    days_to_add = expiry_days
    expiry_date = us_time + timedelta(days=days_to_add)
    print(formatted_date)
    print(expiry_date.strftime("%y%m%d"))

    # Fetch option chain
    option_chain = yf.Ticker(symbol).option_chain()

    available_option_dates = yf.Ticker(symbol).options
  
    # Filter option chain based on expiry date, option type, and maximum price
    options = option_chain.calls if option_type == 'call' else option_chain.puts
    
    options = options[options['lastPrice'] <= max_price]
    options = options[options['contractSymbol'].str.contains(expiry_date.strftime("%y%m%d"))]

    # Find the closest match for the strike price
    closest_strike = options['strike'].iloc[(options['strike'] - predicted_price).abs().idxmin()]
    
    # Filter options based on the closest strike price
    closest_option = options[options['strike'] == closest_strike]

    return closest_option

#try_out = find_option_contract("AAPL", 200, 6, 100, "call")
#print(try_out)

def find_long_straddle(symbol, curr_price, expiry_days, max_price):
    us_timezone = pytz.timezone('America/New_York')
    us_time =  datetime.now(us_timezone)
    formatted_date = us_time.strftime("%y%m%d")
    days_to_add = expiry_days
    expiry_date = us_time + timedelta(days=days_to_add)
    print(formatted_date)
    print(expiry_date.strftime("%y%m%d"))

    # Fetch option chain
    option_chain = yf.Ticker(symbol).option_chain()

    available_option_dates = yf.Ticker(symbol).options
    
    calls = option_chain.calls
    puts = option_chain.puts

    calls = calls[calls['lastPrice'] <= max_price]
    puts = puts[puts['lastPrice'] <= max_price]
    calls = calls[calls['contractSymbol'].str.contains(expiry_date.strftime("%y%m%d"))]
    puts = puts[puts['contractSymbol'].str.contains(expiry_date.strftime("%y%m%d"))]
    
    # Find the closest match for the strike price
    closest_call_strike = calls['strike'].iloc[(calls['strike'] - curr_price).abs().idxmin()]
    closest_put_strike = puts['strike'].iloc[(puts['strike'] - curr_price).abs().idxmin()]
    
    # Filter options based on the closest strike price
    closest_call_option = calls[calls['strike'] == closest_call_strike]
    closest_put_option = puts[puts['strike'] == closest_put_strike]

    res = [closest_call_option, closest_put_option]
    
    return res

#print(find_long_straddle("AAPL", 190, 6, 100))


def find_long_strangle():
    pass


def liquidity_check(symbol, option_type):
    # We can do one for volume of the stock as well. We should do for higher liquidity stocks
    bid_ask_threshold = 0.15
    open_interest_threshold = 100

    option_chain = yf.Ticker(symbol).option_chain()
    options = option_chain.calls if option_type == "call" else option_chain.puts
    oi = options['openInterest'].mean()
    spread = (options['ask']-options['bid']).mean()
    return spread <= bid_ask_threshold and oi >= open_interest_threshold

#print(liquidity_check("AAPL", "call"))



def worth_or_not(symbol, strike_price, implied_vol, expiry_date, call_or_put):
    spot_price = yf.Ticker(symbol).history().iloc[-1]['Close']

    ticker_symbol = "^TNX"  # Replace with the desired Treasury yield ticker symbol - this is 10 year
    treasury_yield = yf.Ticker(ticker_symbol)
    risk_free_rate = treasury_yield.history().iloc[-1]['Close'] / 100

    dividend_rate = 0.0
    #########
    expiration_date = ql.Date(21,7,2023)
    earliest_date = ql.Date(15,7,2023)

    day_count = ql.Actual365Fixed()
    calendar = ql.NullCalendar()
    option_type = ql.Option.Call if call_or_put == "call" else ql.Option.Put
    exercise_type = ql.AmericanExercise(ql.Date(), expiration_date)

    payoff = ql.PlainVanillaPayoff(option_type, int(strike_price))
    #exercise = ql.AmericanExercise(exercise_type)
    option = ql.VanillaOption(payoff, exercise_type)

    spot_handle = ql.QuoteHandle(ql.SimpleQuote(float(spot_price)))
    vol_handle = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(ql.Date(), ql.NullCalendar(), float(implied_vol), day_count))
    
    risk_free_curve = ql.YieldTermStructureHandle(
        ql.FlatForward(0, calendar, risk_free_rate, day_count)
    )

    # Dividend Yield Term Structure
    dividend_yield = ql.YieldTermStructureHandle(
        ql.FlatForward(0, calendar, dividend_rate, day_count)
    )
    
    process = ql.BlackScholesMertonProcess(spot_handle, dividend_yield, risk_free_curve, vol_handle)
    engine = ql.BaroneAdesiWhaleyApproximationEngine(process)

    option.setPricingEngine(engine)

    def greeks_check(option):
        results = dict()
        results['Delta'] = option.delta()
        results['Gamma'] = option.gamma()
        results['Theta'] = option.theta()
        results['Vega'] = option.vega()
        results['Rho'] = option.rho()
        results['Option Price'] = option.NPV()
        return results   

    greeks = greeks_check(option)
    
    return greeks


#print(worth_or_not("AAPL", try_out['strike'], try_out['impliedVolatility'], "123", "call"))

