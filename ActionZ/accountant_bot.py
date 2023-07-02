import pandas as pd
import spreadsheet_bot as bot
import datetime

# prepares a blank PnL template from scratch in case the original is deleted
def create_PnL_template():
    file_name = 'PnL Template'
    
    # detect if there is any file called 'PnL Template'
    accessible_files = bot.spreadsheet_id_dict()
    if file_name in accessible_files:
        print('Existing PnL Template found!')
        print('Deleting old template... ')
        bot.delete_spreadsheet(file_name)
    
    print('Creating PnL template... ')
    bot.create_new_spreadsheet(new_spreadsheet_name = file_name, destination_folder_name='PnL') # create a new google sheets called PnL Template
    
    # set up header and user help
    bot.update_single_cell(file_name = file_name, cell_ID = 'A1', message = 'PnL for <stock_name>')
    bot.update_single_cell(file_name = file_name, cell_ID = 'I3', message = 'NOTE: Transaction_Value is its effect on our balance \n(if we buy a security, it has a negative Transaction_Value, because money goes out of our account) \n(if we sell a security, it has a positive Transaction_Value, because money enters our account)')
    bot.merge(file_name = file_name, start_cell_ID = 'A1', end_cell_ID = 'E1')
    bot.merge(file_name = file_name, start_cell_ID = 'I3', end_cell_ID = 'R5',center = False)
    
    # set up cumulative PnL
    cumulative_PnL = pd.DataFrame().reindex(columns = ['Cumulative_PnL:', '=SUM(D4:D1000)'])
    bot.update_dataframe(file_name = file_name, dataframe = cumulative_PnL, starting_cell_ID='A2')

    # set up column names
    columns_list = ['Transaction_ID', 'Transaction_Datetime', 'Transaction_Type','Transaction_Value']
    columns = pd.DataFrame().reindex(columns = columns_list) # this is how you write a whole row of values btw
    bot.update_dataframe(file_name = file_name, dataframe = columns, starting_cell_ID='A3')
    print('Template successfully created!')
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