from decimal import Decimal
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
from ibapi.order import *
from ibapi.order_condition import Create, OrderCondition
from ibapi.ticktype import TickTypeEnum

auth = json.loads(open('Auth/authDS.txt', 'r').read())

class IBapi(EWrapper, EClient):
	def __init__(self):
		EClient.__init__(self, self)
		self.data = [] #Initialize variable to store candle
		self.contract_details = {} #Contract details will be stored here using reqId as a dictionary key
		self.bardata = {} #Initialize dictionary to store bar
		
	def historicalData(self, reqId, bar):
		print(f'Time: {bar.date} Close: {bar.close}')
		self.data.append([bar.date, bar.close])
		
	def nextValidId(self, orderId: int):
		super().nextValidId(orderId)
		self.nextorderId = orderId
		print('The next valid order id is: ', self.nextorderId)
         
	def orderStatus(self, orderId, status, filled, remaining, avgFullPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
		print('orderStatus - orderid:', orderId, 'status:', status, 'filled', filled, 'remaining', remaining, 'lastFillPrice', lastFillPrice)
	
	def openOrder(self, orderId, contract, order, orderState):
		print('openOrder id:', orderId, contract.symbol, contract.secType, '@', contract.exchange, ':', order.action, order.orderType, order.totalQuantity, orderState.status)

	def execDetails(self, reqId, contract, execution):
		print('Order Executed: ', reqId, contract.symbol, contract.secType, contract.currency, execution.execId, execution.orderId, execution.shares, execution.lastLiquidity)
		
	def contractDetails(self, reqId: int, contractDetails):
		self.contract_details[reqId] = contractDetails

	def get_contract_details(self, reqId, contract):
		self.contract_details[reqId] = None
		self.reqContractDetails(reqId, contract)
		#Error checking loop - breaks from loop once contract details are obtained
		for err_check in range(50):
			if not self.contract_details[reqId]:
				time.sleep(0.1)
			else:
				break
		#Raise if error checking loop count maxed out (contract details not obtained)
		if err_check == 49:
			raise Exception('error getting contract details')
		#Return contract details otherwise
		return app.contract_details[reqId].contract
	
	def updateAccountValue(self, key:str, val:str, currency: str, accountName: str):
		super().updateAccountValue(key, val, currency, accountName)
		print("UpdateAccountValue. Key:", key, "Value:", val,"Currency:", currency, "AccountName:", accountName)

	def updatePortfolio(self, contract: Contract, position: Decimal,marketPrice: float, marketValue: float,averageCost: float, unrealizedPNL: float, realizedPNL: float, accountName: str):
		super().updatePortfolio(contract, position, marketPrice, marketValue,averageCost, unrealizedPNL, realizedPNL, accountName)
		print("UpdatePortfolio.", "Symbol:", contract.symbol, "SecType:", contract.secType, "Exchange:",
			contract.exchange, "Position:", decimalMaxString(position), "MarketPrice:", floatMaxString(marketPrice),
			"MarketValue:", floatMaxString(marketValue), "AverageCost:", floatMaxString(averageCost),
			"UnrealizedPNL:", floatMaxString(unrealizedPNL), "RealizedPNL:", floatMaxString(realizedPNL),
			"AccountName:", accountName)
		
	def updateAccountTime(self, timeStamp: str):
		super().updateAccountTime(timeStamp)
		print("UpdateAccountTime. Time:", timeStamp)
    
	
	def tick_df(self, reqId, contract):
		''' custom function to init DataFrame and request Tick Data '''
		self.bardata[reqId] = pd.DataFrame(columns=['time', 'price'])
		self.bardata[reqId].set_index('time', inplace=True)
		self.reqTickByTickData(reqId, contract, "Last", 0, True)
		return self.bardata[reqId]
	
	def tickByTickAllLast(self, reqId, tickType, time, price, size, tickAtrribLast, exchange, specialConditions):
		if tickType == 1:
			self.bardata[reqId].loc[pd.to_datetime(time, unit='s')] = price

	def position(self, account: str, contract: Contract, position: Decimal,avgCost: float):
		super().position(account, contract, position, avgCost)
		print("Position.", "Account:", account, "Symbol:", contract.symbol, "SecType:",
			contract.secType, "Currency:", contract.currency,
			"Position:", decimalMaxString(position), "Avg cost:", floatMaxString(avgCost))
		
	def pnlSingle(self, reqId: int, pos: Decimal, dailyPnL: float,unrealizedPnL: float, realizedPnL: float, value: float):
		super().pnlSingle(reqId, pos, dailyPnL, unrealizedPnL, realizedPnL, value)
		print("Daily PnL Single. ReqId:", reqId, "Position:", decimalMaxString(pos),
			"DailyPnL:", floatMaxString(dailyPnL), "UnrealizedPnL:", floatMaxString(unrealizedPnL),
			"RealizedPnL:", floatMaxString(realizedPnL), "Value:", floatMaxString(value))

app = IBapi()
app.connect('127.0.0.1', 7497, 123)

def run_loop():
	app.run()
	
app.nextorderId = None
## Need to increment after each order

api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()
time.sleep(1)

#Check if the API is connected via orderid
while True:
	if isinstance(app.nextorderId, int):
		print('connected')
		break
	else:
		print('waiting for connection')
		time.sleep(1)

#Function to create FX Order contract
def FX_order(symbol):
	contract = Contract()
	contract.symbol = symbol[:3]
	contract.secType = 'CASH'
	contract.exchange = 'IDEALPRO'
	contract.currency = symbol[3:]
	return contract

def Stock_contract(symbol, secType='STK', exchange='SMART', currency='USD'):
	''' custom function to create stock contract '''
	contract = Contract()
	contract.symbol = symbol
	contract.secType = secType
	contract.exchange = exchange
	contract.currency = currency
	return contract

def submit_order(contract, direction, qty=100, ordertype='MKT', transmit=True):
	#Create order object
	order = Order()
	order.action = direction
	order.totalQuantity = qty
	order.orderType = ordertype
	order.transmit = transmit
	#submit order
	app.placeOrder(app.nextorderId, contract, order)
	app.nextorderId += 1

def check_for_trade(df, contract):
	start_time = df.index[-1] - pd.Timedelta(minutes=5)
	min_value = df[start_time:].price.min()
	max_value = df[start_time:].price.max()

	if df.price.iloc[-1] < max_value * 0.95:
		submit_order(contract, 'SELL')
		return True

	elif df.price.iloc[-1] > min_value * 1.05:
		submit_order(contract, 'BUY')
		return True

#Create order object
order = Order()
order.action = 'BUY'
order.totalQuantity = 10000
order.orderType = 'LMT'
order.lmtPrice = '1.10'
order.orderId = app.nextorderId
app.nextorderId += 1
order.transmit = False
order.eTradeOnly = False
order.firmQuoteOnly = False



#Create stop loss order object
stop_order = Order()
stop_order.action = 'SELL'
stop_order.totalQuantity = 100000
stop_order.orderType = 'STP'
stop_order.auxPrice = '1.09'
stop_order.orderId = app.nextorderId
app.nextorderId += 1
stop_order.parentId = order.orderId
order.transmit = True

apple_contract = Stock_contract('AAPL')
google_contract = Stock_contract('GOOG')

#Update contract ID
google_contract = app.get_contract_details(101, google_contract)

#Request tick data for google using custom function
df = app.tick_df(401, google_contract)

#Place order
app.placeOrder(app.nextorderId, FX_order('EURUSD'), order)
app.placeOrder(stop_order.orderId, FX_order('EURUSD'), stop_order)
#app.nextorderId += 1

time.sleep(3)

#Cancel order 
print('cancelling order')
app.cancelOrder(app.nextorderId)

apple_contract = Contract()
apple_contract.symbol = 'AAPL'
apple_contract.secType = 'STK'
apple_contract.exchange = 'SMART'
apple_contract.currency = 'USD'

### Options
contract = Contract()
contract.symbol = 'TSLA'
contract.secType = 'OPT'
contract.exchange = 'SMART'
contract.lastTradeDateOrContractMonth = '20201002'
contract.strike = 424
contract.right = 'C'
contract.multiplier = '100'

order = Order()
order.action = 'BUY'
order.totalQuantity = 1
order.orderType = 'MKT'

app.placeOrder(app.nextorderId, contract, order)

for i in range(91):
	print(TickTypeEnum.to_str(i), i) ### We can specify this in reqMktData in the quotations to get the data 

app.reqHistoricalData(1, apple_contract, '', '2 D', '1 hour', 'BID', 0, 2, False, [])
#app.reqMktData(1, apple_contract, '', False, False, [])


#Working with Pandas DataFrames
import pandas

df = pandas.DataFrame(app.data, columns=['DateTime', 'Close'])
df['DateTime'] = pandas.to_datetime(df['DateTime'],unit='s') 
df.to_csv('EURUSD_Hourly.csv')  

print(df)

#time.sleep(10) #Sleep interval to allow time for incoming price data
app.disconnect()

    