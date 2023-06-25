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


from enum import Enum

###useless enums eh

class OptionActions(Enum):
    PUT = 'PUT'
    CALL = 'CALL'

###purely for options trading?

## an "Action" is just defined as a contract + order

def generate_contract(symbol, exchange, target_strike, right='C', multiplier=100):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'OPT' #default
    contract.exchange = exchange

    ##TODO?##
    contract.lastTradeDateOrContractMonth = '20201002'


    contract.strike = target_strike
    contract.right = right
    contract.multiplier = multiplier


    return contract

##creates order without action
def generate_order(quantity, orderType='MKT'):
    order = Order()

    order.totalQuantity = quantity
    order.orderType = orderType

    return order



##I lazy extract this, so I just assume we have an app instance
def perform_call(app, symbol, exchange, target_strike, quantity):
    contract = generate_contract(symbol=symbol, exchange=exchange, target_strike=target_strike)
    order =  generate_order(quantity=quantity)
    order.action = OptionActions.CALL

    app.placeOrder(app.nextorderId, contract, order)

def perform_put(app, symbol, exchange, target_strike, quantity):
    contract = generate_contract(symbol=symbol, exchange=exchange, target_strike=target_strike)
    order =  generate_order(quantity=quantity)
    order.action = OptionActions.PUT

    app.placeOrder(app.nextorderId, contract, order)



