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

auth = json.loads(open('Auth/authDS.txt', 'r').read())

class IBapi(EWrapper, EClient):
     def __init__(self):
         EClient.__init__(self, self) 
         

app = IBapi()
app.connect('127.0.0.1', 7497, 123)

def run_loop():
	app.run()

api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()
time.sleep(1)
apple_contract = Contract()
apple_contract.symbol = 'AAPL'
apple_contract.secType = 'STK'
apple_contract.exchange = 'SMART'
apple_contract.currency = 'USD'

#Request Market Data
#app.reqMktData(1, apple_contract, '', False, False, [])

#time.sleep(10) #Sleep interval to allow time for incoming price data
app.disconnect()
from ibapi.ticktype import TickTypeEnum

for i in range(91):
	print(TickTypeEnum.to_str(i), i)

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


############################################## Telegram Bot - @monymoney_bot ######################################################################
def send_tele_message(message):
    TOKEN = auth["TOKEN"]
    chat_id = auth["chat_id"]
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url).json()


############################################## Pulling Alpha Vantage Data (Stock Data) ######################################################################
def ts_daily_adjusted(ticker,key):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&apikey={key}'
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data["Time Series (Daily)"])
    df = df.iloc[:, :10]
    df = df.transpose()

    symbol = [ticker] * 10
    df.insert(0,'Symbol',symbol)
    df = df.reset_index()
    df = df.rename(columns={'index':'Date'})
    
    return df

def intraday(ticker,key):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={ticker}&interval=5min&apikey={key}"
    r = requests.get(url)
    data = r.json()
    print(data)



############################################## Pulling Alpha Vantage Data (Fundamental) ######################################################################

def balance_sheet(ticker,key):
    url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={key}&datatype=csv"
    r = requests.get(url)
    data = r.json()

    ### To check for what data they have 
    #print(data['annualReports'][0])

    df = pd.DataFrame(data["annualReports"], index=[0,1,2,3,4])
    df = df[['fiscalDateEnding','totalAssets', 'totalCurrentAssets', 'cashAndCashEquivalentsAtCarryingValue', 'cashAndShortTermInvestments', 'inventory', 'currentNetReceivables',
             'totalNonCurrentAssets', 'totalLiabilities', 'totalCurrentLiabilities', 'currentAccountsPayable', 'currentDebt', 'totalNonCurrentLiabilities',
             'retainedEarnings','totalShareholderEquity','totalLiabilities']].iloc[:5]
    #print(df)
    symbol = [ticker] * 5
    df.insert(0,'Symbol',symbol)
    return(df)
    

def cash_flow(ticker,key): 
    url = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker}&apikey={key}"
    r = requests.get(url)
    data = r.json()


    ### To check for what data they have 
    #print(data['annualReports'][0])


    df = pd.DataFrame(data["annualReports"], index=[0,1,2,3,4])
    df = df[['fiscalDateEnding','operatingCashflow', 'capitalExpenditures', 'changeInReceivables','changeInInventory','profitLoss', 'cashflowFromInvestment', 'cashflowFromFinancing','netIncome']].iloc[:5]
    #print(df)
    symbol = [ticker] * 5
    df.insert(0,'Symbol',symbol)
    return(df)

def earnings(ticker,key): 
    url = f"https://www.alphavantage.co/query?function=EARNINGS&symbol={ticker}&apikey={key}"
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data["annualEarnings"], index=[0,1,2,3,4,5,6,7,8,9,10,11,12]).iloc[:5]
    # print(df)
    symbol = [ticker] * 5
    df.insert(0,'Symbol',symbol)
    return(df)
    

def income_statement(ticker,key): 
    url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={key}"
    r = requests.get(url)
    data = r.json()
    
    ### To check for what data they have 
    #print(data['annualReports'][0])


    df = pd.DataFrame(data["annualReports"], index=[0,1,2,3,4])
    df = df[['fiscalDateEnding','grossProfit','totalRevenue','costOfRevenue','ebit','ebitda']].iloc[:5]
    #print(df)
    symbol = [ticker] * 5
    df.insert(0,'Symbol',symbol)
    return(df)

def overview(ticker,key): 
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={key}"
    r = requests.get(url)
    data = r.json()

    
    ### To check for what data they have 
    #print(data)

    df = pd.DataFrame(data, index=[0])
    df = df[['Symbol','Description', 'CIK','MarketCapitalization', 'EBITDA','PERatio', 'PEGRatio','BookValue','DividendYield','TrailingPE','ForwardPE',
             'PriceToBookRatio','EVToRevenue','EVToEBITDA','EPS', "ProfitMargin"]].iloc[:5]
    #print(df)
    return(df)

def earnings_date(ticker,key):
    url = f"https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&symbol={ticker}&horizon=12month&apikey={key}"
    r = requests.get(url)
    decoded_content = r.content.decode('utf-8')
    cr = csv.reader(decoded_content.splitlines(), delimiter=',')
    my_list = list(cr)
    print(my_list)


############################################## Pulling Alpha Vantage Data (Economic Indicators) ######################################################################




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
# send_tele_message("test")