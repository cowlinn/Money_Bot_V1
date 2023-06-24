import yfinance as yf
import pandas as pd

def view_options_data(ticker):
    # Retrieve the Ticker object for the specified ticker
    stock = yf.Ticker(ticker)

    # Retrieve the options chain for the ticker
    options_chain = stock.options
    if options_chain:
        # Create a DataFrame to store the options chain data
        df_calls = pd.DataFrame(columns=['Contract Name', 'Expiry', 'Type', 'Strike', 'Last Price', 'Bid', 'Ask'])
        df_puts = pd.DataFrame(columns=['Contract Name', 'Expiry', 'Type', 'Strike', 'Last Price', 'Bid', 'Ask'])
        # Populate the DataFrame with the options chain data
        for expiry in options_chain:
            options = stock.option_chain(expiry)
            if options.calls is not None:
                calls = options.calls
                df_calls = df_calls.append(calls, ignore_index=True)
            if options.puts is not None:
                puts = options.puts
                df_puts = df_puts.append(puts, ignore_index=True)

        df_calls.to_csv("test_calls_tsla.csv")
        df_puts.to_csv("test_puts_tsla.csv")
        return df_calls, df_puts
    else:
        print("No options chain found for the specified ticker.")

# Example usage
ticker_name = 'TSLA'
options_data = view_options_data(ticker_name)
if options_data is not None:
    print(options_data)
