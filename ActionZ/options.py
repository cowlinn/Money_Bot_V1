import QuantLib as ql
from py_vollib.black_scholes import black_scholes
from py_vollib.black_scholes import implied_volatility
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import requests
import statistics
from optionprice import Option
from binomial_options_pricing import american_fast_tree, optimize_upFactor


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

def find_long_straddle(symbol, atm_strike, expiry_days, max_call_price, max_put_price):
    expiry_date = get_expiry_date(expiry_days)
    expiry_date_string = str(expiry_date).split()[0]
    
    try:
        option_chain = yf.Ticker(symbol).option_chain(expiry_date_string)
    except:
        print(f'No options expiring on {expiry_date_string} found for {symbol}! Try another date or a different ticker symbol!')
        return None

    call_options = option_chain.calls
    put_options = option_chain.puts

    # Filter out call options based on the atm_strike and max_call_price
    call_options = call_options[(call_options['strike'] == atm_strike) & (call_options['lastPrice'] <= max_call_price)]
    
    # Filter out put options based on the atm_strike and max_put_price
    put_options = put_options[(put_options['strike'] == atm_strike) & (put_options['lastPrice'] <= max_put_price)]

    # Merge call and put options DataFrames
    long_straddle = pd.merge(call_options, put_options, on='expiration', suffixes=('_call', '_put'))

    return long_straddle

def get_weekly_std_dev(symbol):
    # Fetch historical stock price data for the past 1 week
    stock_data = yf.download(symbol, period='1wk')['Close']

    # Calculate the standard deviation of the stock's closing prices
    std_dev = statistics.stdev(stock_data)

    return std_dev

## Call and put strike how to price? arbitrary +5/10? MUST BOTH BE OTM - RN Using 1SD
def find_long_strangle(symbol, expiry_days, max_call_price, max_put_price):
    expiry_date = get_expiry_date(expiry_days)
    expiry_date_string = str(expiry_date).split()[0]
    
    try:
        option_chain = yf.Ticker(symbol).option_chain(expiry_date_string)
    except:
        print(f'No options expiring on {expiry_date_string} found for {symbol}! Try another date or a different ticker symbol!')
        return None

    call_options = option_chain.calls
    put_options = option_chain.puts

    std_dev = get_weekly_std_dev(symbol)
    call_strike = int(round(option_chain.info['previousClose'] + std_dev))
    put_strike = int(round(option_chain.info['previousClose'] - std_dev))

    # Filter out call options based on the call_strike and max_call_price
    call_options = call_options[(call_options['strike'] == call_strike) & (call_options['lastPrice'] <= max_call_price)]
    
    # Filter out put options based on the put_strike and max_put_price
    put_options = put_options[(put_options['strike'] == put_strike) & (put_options['lastPrice'] <= max_put_price)]

    # Merge call and put options DataFrames
    long_strangle = pd.merge(call_options, put_options, on='expiration', suffixes=('_call', '_put'))

    return long_strangle


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


## Can use the specific dates as well
def why_go_through_trouble(curr_price, strike_price, iv, risk_free_rate, days_to_expiry, option_type):
    option = Option(european=False,
                          kind=option_type,
                          s0=curr_price,
                          k=strike_price,
                          sigma=iv,
                          r=risk_free_rate,
                          t=days_to_expiry
                          )
    # BSM, MC (Monte carlo), "BT" (Binomial Tree). For MC and BT, need to give iterations
    option_price = option.getPrice(method="BSM")
    option_price = option.getPrice(method="MC", iteration = 500000)
    option_price = option.getPrice(method="BT", iteration = 1000)
    return option_price

# devax(?) all values are 0 eh
# cannot ebe option price also 0 right?
def worth_or_not(symbol, strike_price, implied_vol, expiry_days, call_or_put):
    if not isinstance(strike_price, int):
        strike_price = int(strike_price.iloc[0])
    spot_price = yf.Ticker(symbol).history(period = '1d', interval = '1m').iloc[-1]['Close']

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

    payoff = ql.PlainVanillaPayoff(option_type, strike_price)
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
        # results['Option Price'] = option.NPV()
        optimal_u = optimize_upFactor(symbol = symbol, expiry_days=expiry_days, option_type=call_or_put)
        results['Option Price'] = american_fast_tree(strike_price,expiry_days/365,float(spot_price),risk_free_rate,3, optimal_u, 1/optimal_u, opttype=call_or_put)
        return results   
    # for some reason greeks_check() only work's for calls
    try:
        greeks = greeks_check(option)
        
        return greeks
    except:
        print("DEVAX you probably tried using a put option. Anyway, here's the option pricing using binomial model:")
        results = {}
        optimal_u = optimize_upFactor(symbol = symbol, expiry_days=expiry_days, option_type=call_or_put)
        results['Option Price'] = american_fast_tree(strike_price,expiry_days/365,float(spot_price),risk_free_rate,3, optimal_u, 1/optimal_u, opttype=call_or_put)
        return results   


def get_expiry_date(expiry_days):
    us_timezone = pytz.timezone('America/New_York')
    us_time =  datetime.now(us_timezone)
    days_to_add = expiry_days
    expiry_date = us_time + timedelta(days=days_to_add)
    return expiry_date
# try_out = find_option_contract("SPY", 459, 7, 50, "call")
# print(worth_or_not("SPY", try_out['strike'], try_out['impliedVolatility'], 7, "call"))



# Should we use option price or underlying? If use underlyign need to price the option, if use option then we might keep hitting
def fibonacci_retracement_stop_loss(entry_price_underlying, fixed_retracement_percentage = 61.8):
    # Fibonacci retracement levels (in percentages)
    fibonacci_levels = [23.6, 38.2, 50, 61.8, 76.4]

    # Calculate the stop-loss level based on the fixed retracement percentage
    stop_loss = entry_price_underlying - (entry_price_underlying * (fixed_retracement_percentage / 100))

    return stop_loss

def fibonacci_extension_take_profit(entry_price, fibonacci_extension_percentage = 161.8):
    # Fibonacci extension levels (in percentages)
    fibonacci_extensions = [100, 161.8, 261.8, 423.6]

    # Calculate the take-profit price based on the Fibonacci extension percentage
    take_profit = entry_price + (entry_price * (fibonacci_extension_percentage / 100))

    return take_profit



##### Use Option greeks to price Stop loss / Take profit? How?