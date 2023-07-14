import pandas as pd
import pygsheets
import tempfile
import json
import money_bot_env_reader
# import sys
# import requests

"""
HOW TO USE:
# This bot is currently (25/6/2023) not allowed to create new Google Sheets so meake sure you have created the spreadsheet before using
# UPDATE: (26/6/2023) spreadsheet bot is now able to create and delete Google Sheets. By default, the sheets will be added to the Money_bot folder
# spreadsheet_bot can only delete Google Sheets it created. spreadsheet_bot cannot create new folders

# I tried to implement error handling so you should be able to fix any errors by following the instructions that pop up in console
# It's pretty much a wrapper for pygsheets so whenever we want to write to a google sheets we can just call a single function
# As long as each file and folder has a unique name, we all g (bot will get confused bc I am identifying files and folders by their names)

file_name = 'Test Sheet'

1. Read data from a google sheets into a 2D list
data = read_data(file_name, sheet_number = 0, create_sheets = False)


2. Write to individual cells
message = 'Hello world!'
cell_ID = 'G5'
update_single_cell(file_name, cell_ID, message, sheet_number = 0, create_sheets = False)
# NOTE: to delete data from a cell, just set your message to an empty string ''
# running this line of code should delete your 'Hello world!'
update_single_cell(file_name, cell_ID, '', sheet_number = 0, create_sheets = False)

    2a. We can use a for loop to print stuff too
    # note that this is really REALLY slow so we should use a dataframe or batch update (not implemented yet) if we have large amounts of data to change
    for i in range (1, 27): # note that by default, a google sheets can only have 27 columns
        cell_ID = (1, i)
        cell_ID1 = (i, 1)
        update_single_cell(file_name, cell_ID1, "I'm going downwards!", sheet_number = 0, create_sheets = False)
        update_single_cell(file_name, cell_ID, "I'm going sideways!", sheet_number = 0, create_sheets = False)


3. Write an entire dataframe
import yfinance as yf
import talib

# get some financial data
stock = yf.Ticker('SPY')
data = stock.history(period = '5d', interval = '15m') # historical price data
data.reset_index(inplace=True) # converts datetime to a column
data['ATR'] = talib.ATR(data['High'], data['Low'], data['Close'])

#write the data
update_dataframe(file_name, data, sheet_number = 0, starting_cell_ID = (1,1), create_sheets = False)


4. Create a new blank worksheet in the Google Sheets workbook
sheet_name = 'New Sheet' # name of sheet to be added
file_name = 'Test Sheet' 
add_sheet(file_name, sheet_name = sheet_name)


5. Create a new Google Sheets file and add it to a folder
destination_folder = 'PnL'
new_spreadsheet_name = 'demonstration spreadsheet'
create_new_spreadsheet(new_spreadsheet_name, destination_folder_name = destination_folder)


6. Delete a Google Sheets file created by spreadsheet_bot
file_name = 'demonstration spreadsheet'
delete_spreadsheet(file_name)


7. Merge cells (WARNING: WILL DELETE DATA IN MERGED REGION)
filename = 'Test Sheet'
# remember, we can use A1 or G8 for the starting/ending cells also
starting_cell = (1,1) # top left hand corner of your merge region
ending_cell = (1,4) # bottom left hand corner of your merge region
merge(filename, starting_cell, ending_cell, sheet_number = 0)


8. Unmerge cells (WARNING: WILL DELETE DATA IN MERGED REGION)
filename = 'Test Sheet'
# remember, we can use A1 or G8 for the starting/ending cells also
starting_cell = (1,1) # top left hand corner of your merge region
ending_cell = (1,4) # bottom left hand corner of your merge region
unmerge(filename, starting_cell, ending_cell, sheet_number = 0)


# original file name is the file you want to copy
# copy_file_name is the name that you want to give the copied file
# destination folder is where you want to place the copy
# use this like a linux command (cp filename copyfile .)
9. Copy a file
original_file_name = 'Test Sheet'
copy(original_file_name, copy_file_name = None, destination_folder_name = None)

"""




"""
#####################  exploration  ##########################
#authorization
gc = pygsheets.authorize(service_file='Auth/spreadsheet-bot-390911-5cbd486c0cb1.json')
# sheet_id = '1EZJbt053CN72tLtqxF73tYMSL4xSkfKk-RLbrZ_WZ4Y'

# Create empty dataframe
df = pd.DataFrame()

# Create a column
df['name'] = ['1', '2', '3', '=A2+A3'] # we can even write formulas

#open the google spreadsheet (where 'PY to Gsheet Test' is the name of my sheet)
filename = 'Test Sheet'
try:
    sh = gc.open(filename) # remember to change this if you change the name
except:
    print('Spreadsheet-bot does not have access to '+filename+'!')
    print('Add me as an editor to your Google sheet using the email below and try again.')
    print('spreadsheet-bot@spreadsheet-bot-390911.iam.gserviceaccount.com')
    sys.exit()
    
#select the first sheet 
wks = sh[0] # indexing starts from zero, sheet must be created first, if not this will fail

#update the first sheet with df, starting at cell A1. 
wks.set_dataframe(df,(1,1)) # the tuple is (row, column)
# Update a single cell.
wks.update_value('A1', "Numbers on Stuff")
values = wks.get_all_values() # gets all the values in rows and represents it as a 2D array
row1 = values[0]
row1col1 = values[0][0]
row2col1 = values[1][0] # all values are strings
"""
def _google_creds_as_file():
    auth = money_bot_env_reader.get_env()
    AUTH = {}
    # set up info
    AUTH["type"] = auth["type"]
    AUTH["project_id"] = auth["project_id"]
    AUTH["private_key_id"] = auth["ssb_private_key_id"]
    AUTH["private_key"] = auth["ssb_private_key"]
    AUTH["client_email"] = auth["client_email"]
    AUTH["client_id"] = auth["client_id"]
    AUTH["auth_uri"] = auth["auth_uri"]
    AUTH["token_uri"] = auth["token_uri"]
    AUTH["auth_provider_x509_cert_url"] = auth["auth_provider_x509_cert_url"]
    AUTH["client_x509_cert_url"] = auth["client_x509_cert_url"]
    tfile = tempfile.NamedTemporaryFile(mode="w+", delete=False)
    json.dump(AUTH, tfile)
    tfile.flush()
    return tfile
# creds_file = _google_creds_as_file().name

def print_access_denied_error_msg(file_name):
    print('Spreadsheet-bot does not have access to '+file_name+'!')
    print('Add me as an editor to your google folder using the email below and try again.')
    print('spreadsheet-bot@spreadsheet-bot-390911.iam.gserviceaccount.com')
    error = 'Access Denied'
    print('\nERROR: '+error)
    return error

# tries to access the specified google sheets file. supposed to return some spreadsheet object.
# will return a string 'Access Denied' if could not access
def connect_to_file(file_name):
    # tfile = _google_creds_as_file().name
    gc = pygsheets.authorize(service_file='Auth/spreadsheet-bot-390911-5cbd486c0cb1.json')
    # gc = pygsheets.authorize(service_account_env_var='GDRIVE_API_CREDENTIALS')
    try:
        sh = gc.open(file_name) # remember to change this if you change the name
    except:
        return print_access_denied_error_msg(file_name)
        # sys.exit()
    return sh

def folder_id_dict(client=None):
    if client is None:
        client = pygsheets.authorize(service_file='Auth/spreadsheet-bot-390911-5cbd486c0cb1.json')
    folders = {}
    meta_list = client.drive.list() # get metadata
    for file_meta in meta_list:
        if file_meta['mimeType'] == 'application/vnd.google-apps.folder':
            folders[file_meta['name']] = file_meta['id']
    return folders

def spreadsheet_id_dict(client=None):
    if client is None:
        client = pygsheets.authorize(service_file='Auth/spreadsheet-bot-390911-5cbd486c0cb1.json')
    files = {}
    meta_list = client.drive.list()
    for file_meta in meta_list:
        if file_meta['mimeType'] == 'application/vnd.google-apps.spreadsheet':
            files[file_meta['name']] = file_meta['id']
    return files

# adds a new unamed worksheet to the spreadsheet file sh
# not meant to be called outside of this script!
# if you want to create a named worksheet, call add_sheet() instead!
def create_sheet(sh):
    sheet_name = None
    sh.add_worksheet(sheet_name)

def add_sheet(file_name, sheet_name = None):
    sh = connect_to_file(file_name)
    if isinstance(sh, str):
        return sh
    sh.add_worksheet(sheet_name)

# tries to access the specified sheet. supposed to return some worksheet object.
# will return a string 'Sheet index out of range' if could not access
def access_sheet(sh, sheet_number, create_sheets = False):
    try:
        wks = sh[sheet_number] # indexing starts from zero, sheet must be created first, if not this will fail
    except:
        if not create_sheets:
            print('The specified sheet number does not exist!')
            print('Try creating the sheet first.')
            print('if you would like spreadsheet-bot to create worksheets up to the sheet number you specify, add create_sheets = True as an argument in your function call.')
            print('NOTE: Indexing for spreadsheet-bot starts from 0, not 1!')
            error = 'Sheet index out of range.'
            print('\nERROR: '+error)
            return error
        else:
            create_sheet(sh) # keep creating (adding) sheets until the number of required sheets is met. No filename is specified.
            return access_sheet(sh, sheet_number, create_sheets)
    return wks

# establish connection to a specified sheet in a file
def establish_connection(file_name, sheet_number, create_sheets = False):
    sh = connect_to_file(file_name)
    wks = access_sheet(sh, sheet_number, create_sheets)
    return sh, wks

# returns all the data in the spread sheet in the form of a 2D array
def read_data(file_name, sheet_number = 0):
    sh, wks = establish_connection(file_name, sheet_number)
    if isinstance(sh, str):
        return sh
    if isinstance(wks, str):
        return wks
    data = wks.get_all_values()
    return data

# Edit a single cell in a google sheets that spread-sheet bot has access to
# file_name, message are all strings
# cell_ID can be represented by (row_number, columns) or using the excel notation 'A1'
def update_single_cell(file_name, cell_ID, message, sheet_number = 0, create_sheets = False):
    sh, wks = establish_connection(file_name, sheet_number, create_sheets)
    if isinstance(sh, str):
        return sh
    if isinstance(wks, str):
        return wks
    wks.update_value(cell_ID, message)

# write a dataframe to a google sheets, with the top left hand corner of the data frame starting at start position
# start position is like (rows, columns) so (2,1) is row 2 column 1 or starting from cell_ID 'A2'
def update_dataframe(file_name, dataframe, sheet_number = 0, starting_cell_ID = (1,1), create_sheets = False):
    sh, wks = establish_connection(file_name, sheet_number, create_sheets)
    if isinstance(sh, str):
        return sh
    if isinstance(wks, str):
        return wks
    wks.set_dataframe(dataframe, starting_cell_ID) # the tuple is (row, column)

# delete a file by its filename (spreadsheet_bot is only authorized to delete spreadsheet files)
# if you are already running some code with a spreadsheet object, you can you sh.delete() directly
# NOTE: for now, spreadsheet_bot is only able to delete files it created (must be owner)
def delete_spreadsheet(file_name):
    gc = pygsheets.authorize(service_file='Auth/spreadsheet-bot-390911-5cbd486c0cb1.json')
    spreadsheet_ID = spreadsheet_id_dict(gc)[file_name]
    gc.drive.delete(spreadsheet_ID)

# returns a dictionary where they keys are names of spreadsheets the bot has access to and the values are the folder_ID for the folder that each spreadsheet is in.
def get_sorted_metadata(gc):
    metadata = gc.drive.spreadsheet_metadata() # get metadata of all spreadsheets, including parent folder id
    sorted_metadata = {}
    for i in range(len(metadata)):
        new_key = metadata[i]['name']
        parent_folder_ID_value = metadata[i]['parents'][0] # assume only one parent folder
        sorted_metadata[new_key] = parent_folder_ID_value
    return sorted_metadata

def create_new_spreadsheet(new_spreadsheet_name, destination_folder_name = 'Money_bot'):
    gc = pygsheets.authorize(service_file='Auth/spreadsheet-bot-390911-5cbd486c0cb1.json') # client
    gc.create(new_spreadsheet_name) # create a bew spreadsheet
    new_spreadsheet_ID = spreadsheet_id_dict(gc)[new_spreadsheet_name] # get the id of new spreadsheet
    sorted_metadata = get_sorted_metadata(gc)
    root_parent_folder_ID = sorted_metadata[new_spreadsheet_name]
    try:
        destination_folder_ID = gc.drive.get_folder_id(destination_folder_name)
    except:
        return print_access_denied_error_msg(destination_folder_name)
    gc.drive.move_file(new_spreadsheet_ID, root_parent_folder_ID, destination_folder_ID, body=None)

# NOTE: after merging, the merge cell with have the same ID as the start_cell_ID
# referring to any cells in the merged region besides the starting cell will have no effect
def merge(file_name, start_cell_ID, end_cell_ID, sheet_number = 0, center = True):
    sh, wks = establish_connection(file_name, sheet_number)
    rng = wks.get_values(start_cell_ID, end_cell_ID, returnas='range')
    rng.merge_cells()
    final_cell = wks.cell(start_cell_ID)
    final_cell.set_vertical_alignment(pygsheets.custom_types.VerticalAlignment.MIDDLE)      # always set vertical alignment to middle

    if center:
        final_cell.set_horizontal_alignment(pygsheets.custom_types.HorizontalAlignment.CENTER) # basically merge and center option
        

# NOTE: you have to give the same start_cell_ID and end_cell_ID as the original merged region
# WARNING: merging and unmerging a cell WILL delete values in the merged region! When you unmerge, the value in the merged cell will go to the start_cell_ID coordinate
def unmerge(file_name, start_cell_ID, end_cell_ID, sheet_number = 0):
    sh, wks = establish_connection(file_name, sheet_number)
    rng = wks.get_values(start_cell_ID, end_cell_ID, returnas='range')
    rng.merge_cells(merge_type = 'NONE')

# find the name of a key, given a value
# used to extract names from name:ID dictionaries
def get_key_from_value(dictionary, wanted_val):
    return [k for k,v in dictionary.items() if v == wanted_val][0] # assume no dupicate names


# original file name is the file you want to copy
# copy_file_name is the name that you want to give the copied file
# destination folder is where you want to place the copy
# use this like a linux command (cp filename copyfile .)
def copy(original_file_name, copy_file_name = None, destination_folder_name = None):
    gc = pygsheets.authorize(service_file='Auth/spreadsheet-bot-390911-5cbd486c0cb1.json') # client
    sorted_metadata = get_sorted_metadata(gc)
    folder_ID_dict = folder_id_dict(gc)
    if original_file_name not in sorted_metadata:
        return print_access_denied_error_msg(original_file_name) # bot cannot access file to be copied
    if destination_folder_name is None:
        destination_folder_ID = sorted_metadata[original_file_name] # if no destination folder is specified, copy the file to the same folder as the original
        destination_folder_name = get_key_from_value(folder_ID_dict, destination_folder_ID)
    if destination_folder_name not in folder_ID_dict:
        return print_access_denied_error_msg(destination_folder_name) # bot cannot access the desired destination folder
    destination_folder_ID = gc.drive.get_folder_id(destination_folder_name)
    if copy_file_name is None:
        copy_file_name = original_file_name + '-Copy' # Adds a copy to the end of the name to differentiate (so the bot can tell the difference)
        while copy_file_name in sorted_metadata:
            copy_file_name = copy_file_name + '-Copy' # Adds a copy to the end of the name to differentiate (so the bot can tell the difference)
    destination_folder_ID = gc.drive.get_folder_id(destination_folder_name)
    original_spreadsheet_ID = spreadsheet_id_dict(gc)[original_file_name]
    gc.drive.copy_file(original_spreadsheet_ID, copy_file_name, destination_folder_ID)

