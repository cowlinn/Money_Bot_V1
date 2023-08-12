import sqlite3

# this script has a bunch of functions that handle all the SQLite stuff for the options_decision.py script
# optionType = 'C' for call, 'P' for put
# insert_tuple = (ID, symbol, optionType, buyingPrice, purchaseDate)
# ID = symbol + str(expiry_date) + optionType+str(strike_price)
def write_options_trade_to_db(insert_tuple):
    # create the database file
    conn = sqlite3.connect('options.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS optionsTrades
                      (ID text PRIMARY KEY, 
                       symbol text, 
                       optionType text, 
                       buyingPrice real,
                       date text)''')
    c.execute("INSERT OR REPLACE INTO optionsTrades VALUES (?,?,?,?,?)", insert_tuple)
    conn.commit()
    conn.close()

# returns a list, containing [ID, symbol, optionType, buyingPrice, purchaseDate]
def read_options_trade_from_db_by_symbol(symbol):
    conn = sqlite3.connect('options.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS optionsTrades
                      (ID text PRIMARY KEY, 
                       symbol text, 
                       optionType text, 
                       buyingPrice real,
                       date text)''')
    conn.commit()
    # read db by symbol and return all ID for a given symbol
    c.execute('''SELECT * FROM optionsTrades WHERE symbol=?''', (symbol,))
    output = c.fetchall()
    conn.close()
    return output
    

