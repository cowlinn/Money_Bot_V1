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
    # us_timezone = pytz.timezone('America/New_York')
    # us_time =  datetime.now(us_timezone)
    # formatted_date = us_time.strftime("%y%m%d")
    # days_to_add = expiry_days
    # expiry_date = us_time + timedelta(days=days_to_add)
    # print(formatted_date)
    # print(expiry_date.strftime("%y%m%d"))
    expiry_date = get_expiry_date(expiry_days)
    expiry_date_string = str(expiry_date).split()[0]
    # Fetch option chain for wanted expiry date
    try:
        option_chain = yf.Ticker(symbol).option_chain(expiry_date_string)
    except:
        print(f'No options expiring on {expiry_date_string} found for {symbol}! Try another date or a different ticker symbol!')
        return None
    # available_option_dates = yf.Ticker(symbol).options # redundant, just shows the available expiration dates
  
    # Filter option chain based on expiry date, option type, and maximum price
    options = option_chain.calls if option_type == 'call' else option_chain.puts
    
    # Filter out those that are above our max_price
    options = options[options['lastPrice'] <= max_price]
    # options = options[options['contractSymbol'].str.contains(expiry_date.strftime("%y%m%d"))] # redundant, we already specify contracts that expire on our wanted date above

    # Find the closest match for the strike price
    # if some lines were removed by the previous line of code, this call does not work!
    # closest_strike = options['strike'].iloc[(options['strike'] - predicted_price).abs().idxmin()]

    # instead, reset the index first so it actually starts from 0
    # Find the closest match for the strike price
    options.reset_index(inplace=True)
    closest_strike = int(options['strike'].iloc[(options['strike'] - predicted_price).abs().idxmin()])

    options.index # not sure what this does
    # Filter options based on the closest strike price
    closest_option = options[options['strike'] == closest_strike]

    return closest_option

#try_out = find_option_contract("SPY", 430, 7, 50, "call")
#print(try_out)

def find_long_straddle(symbol, curr_price, expiry_days, max_price):
    expiry_date = get_expiry_date(expiry_days)
    expiry_date_string = str(expiry_date).split()[0]

    # Fetch option chain for wanted expiry date
    try:
        option_chain = yf.Ticker(symbol).option_chain(expiry_date_string)
    except:
        print(f'No options expiring on {expiry_date_string} found for {symbol}! Try another date or a different ticker symbol!')
        return None


    # available_option_dates = yf.Ticker(symbol).options
    
    calls = option_chain.calls
    puts = option_chain.puts

    calls = calls[calls['lastPrice'] <= max_price]
    puts = puts[puts['lastPrice'] <= max_price]

    # calls = calls[calls['contractSymbol'].str.contains(expiry_date.strftime("%y%m%d"))]
    # puts = puts[puts['contractSymbol'].str.contains(expiry_date.strftime("%y%m%d"))]
    
    # Find the closest match for the strike price
    calls.reset_index(inplace=True)
    puts.reset_index(inplace=True)
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


def liquidity_check(symbol, option_type, expiry_days):
    # We can do one for volume of the stock as well. We should do for higher liquidity stocks
    expiry_date = get_expiry_date(expiry_days)
    expiry_date_string = str(expiry_date).split()[0]
    bid_ask_threshold = 0.15
    open_interest_threshold = 100
    try:
        option_chain = yf.Ticker(symbol).option_chain(expiry_date_string) # only look at options for a relevant expiry date?
    except:
        print(f'No options expiring on {expiry_date_string} found for {symbol}! Try another date or a different ticker symbol!')
        return None
    options = option_chain.calls if option_type == "call" else option_chain.puts
    oi = options['openInterest'].mean()
    spread = (options['ask']-options['bid']).mean()
    return spread <= bid_ask_threshold and oi >= open_interest_threshold

#print(liquidity_check("AAPL", "call"))


# devax(?) all values are 0 eh
# cannot ebe option price also 0 right?
def worth_or_not(symbol, strike_price, implied_vol, expiry_days, call_or_put):
    spot_price = yf.Ticker(symbol).history().iloc[-1]['Close']

    ticker_symbol = "^TNX"  # Replace with the desired Treasury yield ticker symbol - this is 10 year
    treasury_yield = yf.Ticker(ticker_symbol)
    risk_free_rate = treasury_yield.history().iloc[-1]['Close'] / 100

    dividend_rate = 0.0
    #########
    expiry_date = get_expiry_date(expiry_days)
    expiry_date_string = str(expiry_date).split()[0]
    year = int(expiry_date_string[:4])
    month = int(expiry_date_string[5:7])
    day = int(expiry_date_string[8:])
    expiration_date = ql.Date(day,month,year)
    # earliest_date = ql.Date(15,7,2023)

    day_count = ql.Actual365Fixed()
    calendar = ql.NullCalendar()
    option_type = ql.Option.Call if call_or_put == "call" else ql.Option.Put
    exercise_type = ql.AmericanExercise(ql.Date(), expiration_date)

    payoff = ql.PlainVanillaPayoff(option_type, int(strike_price.iloc[0]))
    #exercise = ql.AmericanExercise(exercise_type)
    option = ql.VanillaOption(payoff, exercise_type)

    spot_handle = ql.QuoteHandle(ql.SimpleQuote(float(spot_price)))
    vol_handle = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(ql.Date(), ql.NullCalendar(), float(implied_vol.iloc[0]), day_count))
    
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

def get_expiry_date(expiry_days):
    us_timezone = pytz.timezone('America/New_York')
    us_time =  datetime.now(us_timezone)
    days_to_add = expiry_days
    expiry_date = us_time + timedelta(days=days_to_add)
    return expiry_date

#print(worth_or_not("SPY", try_out['strike'], try_out['impliedVolatility'], 7, "call"))

