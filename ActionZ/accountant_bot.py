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
    columns = list_to_df_columns(columns_list)
    bot.update_dataframe(file_name = file_name, dataframe = columns, starting_cell_ID='A3')
    print('Template successfully created!')
    return




# write/update the pnl for a given ticker
# stock_name is a string
# data_to_write is a pandas dataframe or a list
# for a list, it data_to_write should look like [Transaction_ID, Transaction_Datetime, Transaction_Type,Transaction_Value]
# the list should be ordered.

# for a dataframe, data_to_write should look like this:
    
# columns_list = ['Transaction_ID', 'Transaction_Datetime', 'Transaction_Type','Transaction_Value']
# data_to_write = pd.DataFrame()
# data_dict = {} # some dictionary containing transaction data, keys are elements of columns_list, values are lists containing the data
# for i in columns_list:
#     data_to_write[i] = data_dict[i]    
def write_PnL(stock_name, data_to_write):
    current_datetime = datetime.datetime.now()
    current_year = current_datetime.year
    PnL_file_name = stock_name + '-PnL-' + str(current_year)

    accessible_files = bot.spreadsheet_id_dict()
    # check if there is already a PnL spreadsheet for this ticker
    if not PnL_file_name in accessible_files:
        # if no PnL exists, prepare the PnL for this stock
        # check if template exists
        # if no template
        if not 'PnL Template' in accessible_files:
            create_PnL_template()
        # from here onwards, PnL Template exists
        # now we copy the template to start a new PnL for this stock
        bot.copy('PnL Template', PnL_file_name, destination_folder_name='PnL')
        bot.update_single_cell(file_name = PnL_file_name, cell_ID = (1,1), message = 'PnL for ' + stock_name)
    
    # PnL has been created/exists
    read_Data = bot.read_data(PnL_file_name)
    print('Now writing PnL for ' + stock_name)
    
    # find the first empty row from the top
    empty_row = 0
    for row in read_Data:
        empty_row += 1
        if row[0] == '':
            break

    if isinstance(data_to_write, list): # this function can handle list inputs also, for writing just a single row of data
        data_to_write = list_to_df_columns(data_to_write)

    # fill in the appropriate details in the PnL file for this ticker
    if len(data_to_write) == 0: # if we are writing just a single row of data, data_to_write is an empty pd dataframe with the column names as the data
        bot.update_dataframe(file_name = PnL_file_name, dataframe = data_to_write, starting_cell_ID = (empty_row, 1))
        return
    
    # for a bunch of rows of transactions
    rael_data = data_to_write.rename(columns=data_to_write.iloc[0])
    rael_data.drop(index = data_to_write.index[0], axis =0, inplace = True)
    bot.update_dataframe(file_name = PnL_file_name, dataframe = rael_data, starting_cell_ID = (empty_row, 1))


# convert a list into the columns of a dataframe
# returns an empty list
def list_to_df_columns(columns_list):
    df = pd.DataFrame().reindex(columns = columns_list) # this is how you write a single row of values btw
    return df