import sqlite3

# this script has a bunch of functions that handle all the SQLite stuff for the underlyingTA.py script

#################################################### Optimised weights #########################################################
# change optimised_weights list (from weights_optimisation.py) into a single string to store in db as text
def list_to_string(lst):
    return ' '.join(str(i) for i in lst)

# change the stored string from the db into the same format of weights that underlyingTA.py takes
def string_to_list(string):
    lst = string.split()
    return_lst = []
    for i in lst:
        return_lst.append(float(i))
    return return_lst

# insert_tuple = (ID, date, ticker, optimised_weights), ID = date+ticker
def write_weights_to_db(insert_tuple):
    # create the database file
    conn = sqlite3.connect('underlyingTA.db')
    c = conn.cursor()
    # add a table for the weights to go in
    c.execute('''CREATE TABLE IF NOT EXISTS optimisedWeights
                      (ID text PRIMARY KEY, date text, ticker text, weights text)''')

    # # some example data
    # test_date = "2023-07-11"
    # test_ticker = "TSLA"
    # test_weights = "0.4 0.2 0.0 0.0 0.4"
    # ID = test_date + test_ticker
    
    # put the data into a tuple
    # insert_tuple = (ID, test_date, test_ticker, test_weights)
    # inserting weights into db
    c.execute("INSERT OR IGNORE INTO optimisedWeights VALUES (?,?,?,?)", insert_tuple) # ignore because we only want ONE set of optimised weights for each ticker per day
    conn.commit()
    conn.close()
    return
def read_weights_from_db(ID): # ID must be a tuple! 
    # example ID
    # ID = ('2023-07-11SPY',)
    conn = sqlite3.connect('underlyingTA.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS optimisedWeights
                      (ID text PRIMARY KEY, date text, ticker text, weights text)''')
    conn.commit()
    c.execute('''SELECT * FROM optimisedWeights WHERE ID=?''', ID)
    output = c.fetchone()
    conn.close()
    
    # if no such entry
    if output is None:
        return output
    output = string_to_list(output[3])
    return output # returns a usable list of floats for weights to be applied

def read_weights_by_date(date):
    conn = sqlite3.connect('underlyingTA.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS optimisedWeights
                      (ID text PRIMARY KEY, date text, ticker text, weights text)''')
    conn.commit()
    c.execute('''SELECT * FROM optimisedWeights WHERE date=?''', date)
    output = c.fetchall()
    conn.close()
    return output

# reading the data (for visualisation purposes only)
# conn = sqlite3.connect('underlyingTA.db')
# c = conn.cursor()
# for row in c.execute('''SELECT * FROM optimisedWeights'''):
#     print (row)
# conn.close()

# to delete an entry from weights
def delete_weights_from_db(ID): # ID must be a tuple! 
    conn = sqlite3.connect('underlyingTA.db')
    c = conn.cursor()
    c.execute('''DELETE FROM optimisedWeights WHERE ID=?''', ID)
    conn.commit()   
    conn.close()
#################################################### end of Optimised weights #########################################################


#################################################### Trade Actions #########################################################
# insert_tuple = (ID, type, date, datetime, ticker, currentPrice, stoploss, takeprofit), 
# ID = datetime+ticker+type
def write_trade_actions_to_db(insert_tuple):
    conn = sqlite3.connect('underlyingTA.db')
    c = conn.cursor()
    # add a table for the trade actions to go in
    c.execute('''CREATE TABLE IF NOT EXISTS tradeActions
                      (ID text PRIMARY KEY, type text, date text, datetime text, ticker text, currentPrice real, stoploss real, takeprofit real)''')
    c.execute("INSERT OR IGNORE INTO tradeActions VALUES (?,?,?,?,?,?,?,?)", insert_tuple) # ignore because we only want ONE set of optimised weights for each ticker per day
    conn.commit()
    conn.close()

# I don't think we are currently reading this info from the .txt files? but just in case we wanna get the info by hand?
# WARNING: NOT TESTED, MIGHT BE DEVAX
def read_trade_actions_from_db(ID = None, ticker = None, date = None, Type = None): # ID must be a tuple! 
    if ID is None and ticker is None and date is None and Type is None:
        print('Please input search parameters!')
        return
    conn = sqlite3.connect('underlyingTA.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tradeActions
                      (ID text PRIMARY KEY, type text, date text, datetime text, ticker text, currentPrice real, stoploss real, takeprofit real)''')
    conn.commit()
    output_list = []
    if ID is not None:
        c.execute('''SELECT * FROM tradeActions WHERE ID=?''', ID)
        output = c.fetchone()
        output_list.append(output)
    if ticker is not None:
        c.execute('''SELECT * FROM tradeActions WHERE ticker=?''', ticker)
        output = c.fetchall()
        output_list.append(output)
    if date is not None:
        c.execute('''SELECT * FROM tradeActions WHERE date=?''', date)
        output = c.fetchall()
        output_list.append(output)
    if Type is not None:
        c.execute('''SELECT * FROM tradeActions WHERE type=?''', Type)
        output = c.fetchall()
        output_list.append(output)

    conn.close()
    return output # returns a usable list of floats for weights to be applied

# to delete an entry from weights
def delete_trade_actions_from_db_by_id(ID): # ID must be a tuple! 
    conn = sqlite3.connect('underlyingTA.db')
    c = conn.cursor()
    c.execute('''DELETE FROM tradeActions WHERE ID=?''', ID)
    conn.commit()   
    conn.close()

# delete all trade actions for a given date
def delete_trade_actions_from_db_by_date(date): # date must be a tuple! 
    conn = sqlite3.connect('underlyingTA.db')
    c = conn.cursor()
    c.execute('''DELETE * FROM tradeActions WHERE date=?''', date)
    conn.commit()   
    conn.close()
    
# delete all trade actions for a given ticker
def delete_trade_actions_from_db_by_ticker(ticker): # ticker must be a tuple! 
    conn = sqlite3.connect('underlyingTA.db')
    c = conn.cursor()
    c.execute('''DELETE * FROM tradeActions WHERE ticker=?''', ticker)
    conn.commit()   
    conn.close()

