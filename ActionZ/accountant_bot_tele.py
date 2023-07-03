import requests
import json
import telebot
import datetime
import accountant_bot
from telegram import send_tele_message as send_money_bot_message
import spreadsheet_bot as ssb
import random
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
bot = 0
bot = telebot.TeleBot(get_token())

# @bot.message_handler(func=lambda msg: True)
# def echo_all(message):
#     bot.reply_to(message, message.text)

# used by moneybot to send a restart command to cancel out the previous /stopbot
@bot.message_handler(commands=['goodbot'])
def send_thancc(message):
    outcome = random.random()
    if outcome <= 0.5:
        bot.reply_to(message, "Mmm... Thanks for your praise zaddy.\U0001F4A6\U0001F4A6\U0001F48B\U0001F346\U0001F4A6\U0001F4A6")
    elif outcome > 0.5:
        bot.reply_to(message, "Thank you sir! 🫡")

@bot.message_handler(commands=['restart'])
def send_restart(message):
    bot.reply_to(message, "Bot restarted.")

@bot.message_handler(commands=['dailysummary'])
def send_dsummary(message):
    bot.reply_to(message, "Daily summary requested.")
    
@bot.message_handler(commands=['yearlysummary'])
def send_ysummary(message):
    bot.reply_to(message, "Year to date summary requested.")

@bot.message_handler(commands=['stocksummary'])
def send_ssummary(message):
    command_args = message.text.split()[1:]
    current_datetime = datetime.datetime.now()
    current_year = str(current_datetime.year)
    accessible_files = ssb.spreadsheet_id_dict()
    if len(command_args) == 0:
        bot.reply_to(message, "No stocks specified! \nUsage: /stocksummary <stock_name1> <stock_name2>")

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
                bot.reply_to(message, f"PnL for {stock_name} exists but has no entries yet!")
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
            bot.reply_to(message, f"Stock summary for {stock_name} requested. \nYour current cumulative PnL for {stock_name} is USD ${cumulative_PnL}. \nThe largest transaction we made was a {largest_transaction_type}, dated {largest_transaction_date}, with ID {largest_transaction_ID}, giving us a {effect} of USD ${largest_transaction_value}. \nYour most recent trasaction has ID {latest_transaction_data[0]}, occured on {latest_transaction_data[1]}, was a {latest_transaction_data[2]} and had a value of {latest_transaction_data[3]}.")
        elif file_to_access not in accessible_files:
            bot.reply_to(message, "Stock summary for "+stock_name+" requested. \nNo PnL for this stock exists!")


# stops the infinity_polling loop
# we need to stop the bot if we want to edit the code
# we might want to store the state of the bot (running or not) in some .txt
# so we can have code that checks if the bot has been stopped, if stopped, start it again
@bot.message_handler(commands=['stopbot'])
def stop_NOW(message):
    bot.stop_bot()
    bot.reply_to(message, "HL says BYEBYE, bot now stopping.")
    send_money_bot_message("/restart") # so that the next time the bot starts polling it won't just read the /stopbot command and immediately shut down
    

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