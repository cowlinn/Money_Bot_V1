import requests
import json
import telebot
import datetime
from telegram import send_tele_message as send_money_bot_message
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
bot = telebot.TeleBot(get_token())

# @bot.message_handler(func=lambda msg: True)
# def echo_all(message):
#     bot.reply_to(message, message.text)

# used by moneybot to send a restart command to cancel out the previous /stopbot
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
    for stock_name in command_args:
        # run some code to get the summary data
        bot.reply_to(message, "Stock summary for "+stock_name+" requested.")
        

# stops the infinity_polling loop
# we need to stop the bot if we want to edit the code
@bot.message_handler(commands=['stopbot'])
def stop_NOW(message):
    bot.stop_bot()
    bot.reply_to(message, "HL says BYEBYE, bot now stopping.")
    send_money_bot_message("/restart")
    

# # Define your webhook endpoint
# @app.route('/your-webhook-endpoint', methods=['POST'])
# def webhook():
#     update = telebot.types.Update.de_json(request.get_json(force=True))
#     bot.process_new_updates([update])
#     return 'OK', 200

# for now we use this inifite polling loop
# I tried to look into webhooks but it seems like its just this with extra steps
def run():
    bot.infinity_polling()
# we might want to poll for like a few hours only? we can have some other script start the loop also