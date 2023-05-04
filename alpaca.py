import pandas as pd
import datetime
from datetime import datetime as dt
from pytz import timezone
import time
import alpaca_trade_api as alpaca
import json
import smtplib
from datetime import timedelta
import os.path
import requests

## Alpaca Auth
auth = json.loads(open('Auth/auth.txt', 'r').read())
api = alpaca.REST(auth['ALPACA-API-KEY-ID'], auth['ALPACA-API-SECRET-KEY'], base_url='https://paper-api.alpaca.markets')
tickers = open('Auth/test_tickers.txt', 'r').read()
tickers = tickers.upper().split()
global TICKERS 
TICKERS = tickers

# for ticker in TICKERS:    
#     order_buy = api.submit_order(ticker, qty=1, side='buy')

for p in api.list_positions():
    print(p)

## Telegram Bot - @monymoney_bot

TOKEN = "6230571803:AAEZ7Vh7LjabCl2b0S8JDyVXnaE8PRB7ndQ"
chat_id = "560714019"
message = "hello from your telegram bot"
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
print(requests.get(url).json())