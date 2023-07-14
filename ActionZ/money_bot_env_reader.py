from dotenv import dotenv_values, load_dotenv
import os

def get_env(env_file = "money_bot.env"):
    current_wd = os.getcwd()
    fullpath = os.path.join(current_wd, env_file)
    config = dotenv_values(fullpath)
    # for i in config:
    #     print(i)
    #     print (config[i])
    return config

def load_env(env_file = "money_bot.env"):
    current_wd = os.getcwd()
    fullpath = os.path.join(current_wd, env_file)
    load_dotenv(fullpath)