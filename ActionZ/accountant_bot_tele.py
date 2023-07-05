import requests
import json
import telebot
import datetime
# import accountant_bot
import time
import spreadsheet_bot as ssb
import random
import os
import yfinance as yf
# from flask import Flask, request

def get_token():
    auth = json.loads(open('Auth/accountant_auth.txt', 'r').read())
    token = auth["TOKEN"]
    return token

def send_tele_message(message, chat_name = 'money_bot_trades', auth = json.loads(open('Auth/accountant_auth.txt', 'r').read())):
    TOKEN = auth["TOKEN"]
    if chat_name == 'money_bot_trades':
        chat_id = auth["bot_chat_id"]
    elif chat_name == 'money_bot':
        chat_id = auth["main_chat_id"]
    else:
        print('No valid chat_name specified.')
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}&disable_notification=true"
    requests.get(url).json()
    
# Create a Flask web application
# app = Flask(__name__)

# initialize bot
bot = telebot.TeleBot(get_token(),last_update_id=0)
# get last update ID and re-initialize so it doesn't read every update
last_update_id = bot.get_updates()[-1].update_id
bot = telebot.TeleBot(get_token(),last_update_id=last_update_id)

# @bot.message_handler(func=lambda msg: True)
# def echo_all(message):
#     bot.reply_to(message, message.text)

# used by moneybot to send a restart command to cancel out the previous /stopbot


@bot.message_handler(commands=['help'])
def send_halp(message):
    bot.reply_to(message, "Here’s a list of commands currently implemented for accountant_bot: \n/stocksummary <stock_name1> <stock_name2> - this gives a summary of all stocks requested. \n/yearlysummary - this gives a summary across all stocks for the current year. You can specify the year as an optional argument if desired. \n/dailysummary - this gives a summary of all the trades we did in the most recent trading day across all stocks. A date can be specified in the format yyyy-mm-dd if you want to check our transactions on a certain date. \n/stopbot - stops the infinite polling and shuts the bot down. This is necessary if we want to edit the code for this bot. \n/goodbot - praises the bot.", disable_notification=True)

@bot.message_handler(commands=['goodbot'])
def send_thancc(message):
    outcome = random.random()
    if outcome <= 0.5:
        bot.reply_to(message, "Mmm... Thanks for your praise zaddy.\U0001F4A6\U0001F4A6\U0001F48B\U0001F346\U0001F4A6\U0001F4A6", disable_notification=True)
    elif outcome > 0.5:
        bot.reply_to(message, "Thank you sir! 🫡", disable_notification=True)

@bot.message_handler(commands=['restart'])
def send_restart(message):
    bot.reply_to(message, "Bot restarted.", disable_notification=True)

@bot.message_handler(commands=['dailysummary'])
def send_dsummary(message):
    command_args = message.text.split()[1:]
    if not command_args:
        data = yf.Ticker('SPY').history(period = '1d', interval = '1d')
        data.reset_index(inplace=True)
        last_trading_day = str(data['Date']).split()[1]
    elif len(command_args) > 1:
        bot.reply_to(message, "Please specify one date at a time!", disable_notification=True)
        return
    elif len(command_args) == 1:
        last_trading_day = command_args[0]
    wantedYear = last_trading_day[:4]
    bot.reply_to(message, f"Daily summary requested. Currently accessing available PnL sheets for {wantedYear}, please wait.", disable_notification=True)
    accessible_files = ssb.spreadsheet_id_dict()
    current_year_list_of_PnL = []
    for sheet_name in accessible_files:
        if sheet_name.endswith(f'-PnL-{wantedYear}'):
            current_year_list_of_PnL.append(sheet_name)
    if not current_year_list_of_PnL:
        bot.send_message(message.chat.id, f"No PnLs for year {wantedYear} found! \nPlease enter a valid date!", disable_notification=True)
        return
    
    daily_cumulative_PnL = 0 # overall PnL for a given day
    stock_name_to_stock_daily_cumulative_PnL = {} # cumulative PnL for the respective stonks
    stock_name_list = []
    for sheet_name in current_year_list_of_PnL:
        data = ssb.read_data(sheet_name)
        stock_name = data[0][0].split()[-1]
        stock_daily_cumulative_PnL = 0        
        for row in range(3, len(data)):
            if data[row][0] == '':
                break
            if data[row][1][:10] == last_trading_day:
                daily_cumulative_PnL += float(data[row][3])
                stock_daily_cumulative_PnL += float(data[row][3])
        if stock_daily_cumulative_PnL != 0:
            stock_name_to_stock_daily_cumulative_PnL[stock_name] = stock_daily_cumulative_PnL
            stock_name_list.append(stock_name)
    if not stock_name_to_stock_daily_cumulative_PnL:
        bot.send_message(message.chat.id, f"No recorded transactions on {last_trading_day}!", disable_notification=True)
        return
    biggest_winner = max(stock_name_to_stock_daily_cumulative_PnL, key=stock_name_to_stock_daily_cumulative_PnL.get)
    biggest_PnL = str(stock_name_to_stock_daily_cumulative_PnL[biggest_winner])
    biggest_loser = min(stock_name_to_stock_daily_cumulative_PnL, key=stock_name_to_stock_daily_cumulative_PnL.get)
    smallest_PnL = str(stock_name_to_stock_daily_cumulative_PnL[biggest_loser])
    
    stock_name_str = ', '.join(stock_name_list)

    if daily_cumulative_PnL >= 0:
        bot.send_message(message.chat.id, f"We had trades for the following stocks on {last_trading_day}: \n{stock_name_str} \nAcross these stocks, we had a cumulative profit of {daily_cumulative_PnL} USD. \nGreat job! Keep it up and we go to da moon! \nYour biggest winner was {biggest_winner} with a cumulative PnL of {biggest_PnL} USD and your biggest loser was {biggest_loser} with a cumulative PnL of {smallest_PnL} USD.", disable_notification=True)
    if daily_cumulative_PnL < 0:
        bot.send_message(message.chat.id, f"We had trades for the following stocks on {last_trading_day}: \n{stock_name_str} \nAcross these stocks, we had a cumulative loss of {daily_cumulative_PnL} USD. \nBad job! Please work on your algo or something or we are going bankrupt. \nYour biggest winner was {biggest_winner} with a cumulative PnL of {biggest_PnL} USD and your biggest loser was {biggest_loser} with a cumulative PnL of {smallest_PnL} USD.", disable_notification=True)

@bot.message_handler(commands=['yearlysummary'])
def send_ysummary(message):
    command_args = message.text.split()[1:]
    current_datetime = datetime.datetime.now()
    if not command_args:
        current_year = str(current_datetime.year)
    elif len(command_args) > 1:
        bot.reply_to(message, "Please specify one year at a time!", disable_notification=True)
        return
    elif len(command_args) == 1:
        current_year = command_args[0]
    bot.reply_to(message, f"Year to date summary requested. Currently accessing available PnL sheets for {current_year}, please wait.", disable_notification=True)
    accessible_files = ssb.spreadsheet_id_dict()
    current_year_list_of_PnL = []
    # get current PnLs
    for sheet_name in accessible_files:
        if sheet_name.endswith(f'-PnL-{current_year}'):
            current_year_list_of_PnL.append(sheet_name)
    if not current_year_list_of_PnL:
        bot.send_message(message.chat.id, f"No PnLs for year {current_year} found! \nPlease enter a valid year!", disable_notification=True)
        return
    total_cumulative_PnL = 0
    stock_name_list = []
    stock_name_to_cumulative_PnL_dict = {}
    for sheet_name in current_year_list_of_PnL:
        data = ssb.read_data(sheet_name)
        total_cumulative_PnL += float(data[1][1])
        stock_name = data[0][0].split()[-1]
        stock_name_list.append(stock_name)
        stock_name_to_cumulative_PnL_dict[stock_name] = float(data[1][1])
    
    biggest_winner = max(stock_name_to_cumulative_PnL_dict, key=stock_name_to_cumulative_PnL_dict.get)
    biggest_PnL = str(stock_name_to_cumulative_PnL_dict[biggest_winner])
    biggest_loser = min(stock_name_to_cumulative_PnL_dict, key=stock_name_to_cumulative_PnL_dict.get)
    smallest_PnL = str(stock_name_to_cumulative_PnL_dict[biggest_loser])
    # stock_name_str = stock_name_list[0]
    # for stock_name in range(1, len(stock_name_list)):
    #     stock_name_str += ', '+stock_name
    stock_name_str = ', '.join(stock_name_list)
    total_PnL = str(total_cumulative_PnL)
    if total_cumulative_PnL >= 0:
        bot.send_message(message.chat.id, f"We have PnL for the following stocks: \n{stock_name_str} \n Across these stocks, we have a cumulative profit of {total_PnL} USD. \nGreat job! Keep it up and we go to da moon! \nYour biggest winner was {biggest_winner} with a cumulative PnL of {biggest_PnL} USD and your biggest loser was {biggest_loser} with a cumulative PnL of {smallest_PnL} USD.", disable_notification=True)
    elif total_cumulative_PnL < 0:
        bot.send_message(message.chat.id, f"We have PnL for the following stocks: \n{stock_name_str} \n Across these stocks, we have a cumulative loss of {total_PnL} USD. \nBad job! Please work on your algo or something or we are going bankrupt. \nYour biggest winner was {biggest_winner} with a cumulative PnL of {biggest_PnL} USD and your biggest loser was {biggest_loser} with a cumulative PnL of {smallest_PnL} USD.", disable_notification=True)

@bot.message_handler(commands=['stocksummary'])
def send_ssummary(message):
    command_args = message.text.split()[1:]
    current_datetime = datetime.datetime.now()
    current_year = str(current_datetime.year)
    accessible_files = ssb.spreadsheet_id_dict()
    if not command_args:
        bot.reply_to(message, "No stocks specified! \nUsage: /stocksummary <stock_name1> <stock_name2>", disable_notification=True)

    for stock_name in command_args:
        file_to_access = f'{stock_name}-PnL-{current_year}'
        # run some code to get the summary data
        if file_to_access in accessible_files:
            data = ssb.read_data(file_to_access)
            cumulative_PnL = data[1][1] # this is a string
            transaction_ID_to_transaction_value_dict = {}
            last_row_of_content = 2 # we are ignoring the first 3 rows of headers
            for row in range(3, len(data)):
                if data[row][0] == '': # stop iterating if no more data
                    break
                last_row_of_content += 1
                for col in range(4):
                    transaction_ID = data[row][0]
                    transaction_value = data[row][3]
                    transaction_ID_to_transaction_value_dict[transaction_ID] = abs(float(transaction_value))
            if not transaction_ID_to_transaction_value_dict:
                bot.reply_to(message, f"PnL for {stock_name} exists but has no entries yet!", disable_notification=True)
                break
            # get largest transaction
            largest_transaction_ID = max(transaction_ID_to_transaction_value_dict, key=transaction_ID_to_transaction_value_dict.get)
            
            for row in data:
                if row[0] == largest_transaction_ID:
                    largest_transaction_date = row[1]
                    largest_transaction_type = row[2]
                    largest_transaction_value = row[3]
            if float(largest_transaction_value)>0:
                effect = 'gain'
            else:
                effect = 'loss'
            latest_transaction_data = data[last_row_of_content]
            bot.reply_to(message, f"Stock summary for {stock_name} requested. \nYour current cumulative PnL for {stock_name} is {cumulative_PnL} USD. \nThe largest transaction we made was a {largest_transaction_type}, dated {largest_transaction_date}, with ID {largest_transaction_ID}, giving us a {effect} of {largest_transaction_value} USD. \nYour most recent trasaction has ID {latest_transaction_data[0]}, occured on {latest_transaction_data[1]}, was a {latest_transaction_data[2]} and had a value of {latest_transaction_data[3]} USD.", disable_notification=True)
        elif file_to_access not in accessible_files:
            bot.reply_to(message, "Stock summary for "+stock_name+" requested. \nNo PnL for this stock exists!", disable_notification=True)


# stops the infinity_polling loop
# we need to stop the bot if we want to edit the code
# we might want to store the state of the bot (running or not) in some .txt
# so we can have code that checks if the bot has been stopped, if stopped, start it again
@bot.message_handler(commands=['stopbot'])
def stop_NOW(message):
    bot.stop_bot()
    bot.reply_to(message, "HL says BYEBYE, bot now stopping.", disable_notification=True)
    # write a file that contains the update ID of the most recent /stop command
    # fullpath = 'accountant_bot_tele_last_update_id.txt'
    # update_id_file = open(fullpath, "w")
    # update_ID = str(message.update_id)
    # print(update_ID)
    # update_id_file.write(update_ID)
    # update_id_file.close()
    
    # apparently the bot cannot see commands from other bots?
    # send_money_bot_message("/restart") # so that the next time the bot starts polling it won't just read the /stopbot command and immediately shut down
    

# # Define your webhook endpoint
# @app.route('/your-webhook-endpoint', methods=['POST'])
# def webhook():
#     update = telebot.types.Update.de_json(request.get_json(force=True))
#     bot.process_new_updates([update])
#     return 'OK', 200

# for now we use this inifite polling loop
# I tried to look into webhooks but it seems like its just this with extra steps
# the run() is not working also idk why
def run():
    # initialize bot
    bot = telebot.TeleBot(get_token())
    bot.infinity_polling()
bot.infinity_polling()

# we might want to poll for like a few hours only? we can have some other script start the loop also