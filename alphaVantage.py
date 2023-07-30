import pandas as pd
import datetime
from datetime import datetime as dt
from pytz import timezone
import threading
import time
import json
import smtplib
from datetime import timedelta
import os.path
import requests
import csv
import ibapi
from ibapi.client import EClient
from ibapi.wrapper import EWrapper  
from ibapi.contract import Contract
import finnhub
import yfinance as yf

##### Alpha Vantage API Keys ######
apiKey = "YU2WS3DFRZNOBW2Q"
apiKey2= '7E01NY5AWTMML6AR'
apiKey3 = 'TMJXU8UWCA0PYW4I'
apiKey4 = 'GMORUOA5ANFIFLYB'
apiKey5 = '6J3WYMQU1IBGY8JT'
apiKey6 = 'Q7S5MY8BOZ30WU9F'
apiKey7 = 'E7RSATAZGN09U7BF'
apiKey8 = 'OJ3HYOQ5R6YQQ7HQ'
apiKey9 = 'RXNCYRXC8HRE67VZ'
apiKey10 ='4IZ6YCBLPVN2WF87'
apiKey11 ='T16XJ7L29ZIC54F5'
apiKey12 = 'T8KDAAX3DMF90GU8'
apiKey13 = 'YPB0AWLC04BSYLCA'
apiKey14 = 'IIDIQCUR0VQHF2K9'
apikeys = [apiKey,apiKey2,apiKey3,apiKey4,apiKey5,apiKey6,apiKey7,apiKey8,apiKey10,apiKey11,apiKey12,apiKey13,apiKey14]

##### Finnhub API Keys ######
finnhub_client = finnhub.Client(api_key="civscj1r01qu45tmlivgcivscj1r01qu45tmlj00")

## Machine learning here? (Economic data)
## Webscrape quiver quant



############################################## COMPANY USE ###############################################################################################

def company_wise(stock_symbol, weeks_back=2, days_to_check=7):
    # Fetch historical stock price data

    today = datetime.now().date()
    end_date = today + timedelta(days=days_to_check)

    date = next_earnings_date(stock_symbol, "7E01NY5AWTMML6AR")
    EARNINGS_CHECK = today <= date <= end_date

    insider_data = insider_sentiment(stock_symbol)

    overview_data = overview(stock_symbol, "YPB0AWLC04BSYLCA")

    stock_data = yf.download(stock_symbol, period='1w')
    percent_change_1w = ((stock_data['Close'][-1] - stock_data['Close'][0]) / stock_data['Close'][0]) * 100
    stock_data_2w = yf.download(stock_symbol, period='2w')
    percent_change_2w = ((stock_data_2w['Close'][-1] - stock_data_2w['Close'][0]) / stock_data_2w['Close'][0]) * 100
    
    # Get the fear greed index - IS THIS FOR MARKET OR FOR COMPANY? - USE A LIBRARY
    fear_greed = fgi.fear_greed_index()

    if percent_change_1w > 2 and percent_change_2w > 5 and fear_greed >= 90:
        print("Market has been going up alot for the past week and two weeks, and fear greed index is at 100 (Extreme greed). Avoid playing with options this week.")
        return False
    else:
        print("Conditions seem favorable for options trading this week.")
        return True
    

def next_earnings_date(ticker,key):
    url = f"https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&symbol={ticker}&horizon=12month&apikey={key}"
    r = requests.get(url)
    decoded_content = r.content.decode('utf-8')
    cr = csv.reader(decoded_content.splitlines(), delimiter=',')
    my_list = list(cr)[1][2]
    print(my_list)


## -100 for negative ot 100 for positive
def insider_sentiment(ticker):

    current_date = dt.now().date()
    two_months_ago = current_date - timedelta(days=60)

    start_date_str = two_months_ago.strftime('%Y-%m-%d')
    end_date_str = current_date.strftime('%Y-%m-%d')


    print(finnhub_client.stock_insider_sentiment(ticker, two_months_ago, current_date))


def overview(ticker,key): 
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={key}"
    r = requests.get(url)
    data = r.json()

    df = pd.DataFrame(data, index=[0])
    df = df[['Symbol','Description', 'CIK','MarketCapitalization', 'EBITDA','PERatio', 'PEGRatio','BookValue','DividendYield','TrailingPE','ForwardPE',
             'PriceToBookRatio','EVToRevenue','EVToEBITDA','EPS', "ProfitMargin"]].iloc[:5]
    #print(df)
    return(df)


############################################## MARKET USE ##########################################################################################

# Consider VIX? 

def market_wise():

    # economic_events = {+
    #     "2023-08-01": "Unemployment Rate Release",
    #     "2023-08-02": "GDP Growth Report",
    #     "2023-08-03": "Interest Rate Decision",
    #     # Add more economic events and their dates here
    # }

    # for event_date, event_name in economic_events.items():
    #     event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
    #     if today <= event_date <= end_date:
    #         print(f"Upcoming Economic Event: {event_name} on {event_date}.")
    #         break
    # else:
    #     print("No significant economic events scheduled within the specified time range.")

    pass

def real_gdp_per_capita(key):
    url = f'https://www.alphavantage.co/query?function=REAL_GDP_PER_CAPITA&apikey={key}'
    r = requests.get(url)
    data = r.json()


def treasury_yield(key):
    url = f'https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=monthly&maturity=10year&apikey={key}'
    r = requests.get(url)
    data = r.json()

def interest_rate(key):
    url = f'https://www.alphavantage.co/query?function=FEDERAL_FUNDS_RATE&interval=monthly&apikey={key}'
    r = requests.get(url)
    data = r.json()

def cpi(key):
    url = f'https://www.alphavantage.co/query?function=CPI&interval=monthly&apikey={key}'
    r = requests.get(url)
    data = r.json()

def inflation(key):
    url = f'https://www.alphavantage.co/query?function=INFLATION&apikey={key}'
    r = requests.get(url)
    data = r.json()

def global_commodities_index(key):
    url = f'https://www.alphavantage.co/query?function=ALL_COMMODITIES&interval=monthly&apikey={key}'
    r = requests.get(url)
    data = r.json()

def news_and_sentiment(ticker,key):
    url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={key}'
    r = requests.get(url)
    data = r.json()


############################################## Pulling Alpha Vantage Data (Technical Indicators) ######################################################################

def macd(ticker,key):
    url = f'https://www.alphavantage.co/query?function=MACD&symbol={ticker}&interval=daily&series_type=open&apikey={key}'
    r = requests.get(url)
    data = r.json()

    df = pd.DataFrame(data["Technical Analysis: MACD"])
    df = df.iloc[:, :10]
    df = df.transpose()

    symbol = [ticker] * 10
    df.insert(0,'Symbol',symbol)
    df = df.reset_index()
    df = df.rename(columns={'index':'Date'})
    return df

def adxr(ticker,key):
    url = f'https://www.alphavantage.co/query?function=ADXR&symbol={ticker}&interval=daily&time_period=10&apikey={key}'
    r = requests.get(url)
    data_adx = r.json()

    df_adx = pd.DataFrame(data_adx["Technical Analysis: ADXR"])
    df= df_adx.iloc[:, :10]
    df = df.transpose()

    symbol = [ticker] * 10
    df.insert(0,'Symbol',symbol)
    df = df.reset_index()
    df = df.rename(columns={'index':'Date'})
    return df


def obv(ticker,key):
    url = f'https://www.alphavantage.co/query?function=OBV&symbol={ticker}&interval=daily&apikey={key}'
    r = requests.get(url)
    data = r.json()

    df = pd.DataFrame(data["Technical Analysis: OBV"])
    df= df.iloc[:, :10]
    df = df.transpose()

    symbol = [ticker] * 10
    df.insert(0,'Symbol',symbol)
    df = df.reset_index()
    df = df.rename(columns={'index':'Date'})
    return df

def stochRSI(ticker,key):
    url = f'https://www.alphavantage.co/query?function=STOCHRSI&symbol={ticker}&interval=daily&time_period=10&series_type=close&fastkperiod=6&fastdmatype=1&apikey={key}'
    r = requests.get(url)
    data = r.json()

    df = pd.DataFrame(data["Technical Analysis: STOCHRSI"])
    df = df.iloc[:, :10]
    df = df.transpose()

    symbol = [ticker] * 10
    df.insert(0,'Symbol',symbol)
    df = df.reset_index()
    df = df.rename(columns={'index':'Date'})
    return df

def sma(ticker,key):
    url = f'https://www.alphavantage.co/query?function=SMA&symbol={ticker}&interval=daily&time_period=10&series_type=open&apikey={key}'
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data["Technical Analysis: SMA"])
    df = df.iloc[:, :10]
    df = df.transpose()

    symbol = [ticker] * 10
    df.insert(0,'Symbol',symbol)
    df = df.reset_index()
    df = df.rename(columns={'index':'Date'})
    return df

def ema50(ticker,key):
    url = f'https://www.alphavantage.co/query?function=EMA&symbol={ticker}&interval=daily&time_period=50&series_type=open&apikey={key}'
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data["Technical Analysis: EMA"])
    df = df.iloc[:, :10]
    df = df.transpose()

    symbol = [ticker] * 10
    df.insert(0,'Symbol',symbol)
    df = df.reset_index()
    df = df.rename(columns={'index':'Date'})

    return df

def ema100(ticker,key):
    url = f'https://www.alphavantage.co/query?function=EMA&symbol={ticker}&interval=daily&time_period=100&series_type=open&apikey={key}'
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data["Technical Analysis: EMA"])
    df = df.iloc[:, :10]
    df = df.transpose()

    symbol = [ticker] * 10
    df.insert(0,'Symbol',symbol)
    df = df.reset_index()
    df = df.rename(columns={'index':'Date'})

    return df

def ema200(ticker,key):
    url = f'https://www.alphavantage.co/query?function=EMA&symbol={ticker}&interval=daily&time_period=200&series_type=open&apikey={key}'
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data["Technical Analysis: EMA"])
    df = df.iloc[:, :10]
    df = df.transpose()

    symbol = [ticker] * 10
    df.insert(0,'Symbol',symbol)
    df = df.reset_index()
    df = df.rename(columns={'index':'Date'})
    
    return df

def wma(ticker,key):
    url = f'https://www.alphavantage.co/query?function=WMA&symbol={ticker}&interval=daily&time_period=10&series_type=open&apikey={key}'
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data["Technical Analysis: WMA"])
    df = df.iloc[:, :10]
    df = df.transpose()

    symbol = [ticker] * 10
    df.insert(0,'Symbol',symbol)
    df = df.reset_index()
    df = df.rename(columns={'index':'Date'})
    return df