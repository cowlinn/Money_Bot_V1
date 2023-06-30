import pandas as pd
import spreadsheet_bot as bot

# prepares a blank PnL template from scratch in case the original is deleted
def create_PnL_template():
    print('Creating PnL template... ')
    return

# write/update the pnl for a given ticker
def write_PnL(stock_name):
    # check if there is already a PnL spreadsheet for this ticker
    
    # if no PnL exists, check if template exists, then create the PnL
    # if no template
    create_PnL_template()
    
    # copy the template
    bot.copy()
    
    # fill in the appropriate details in the PnL file for this ticker
    
    return