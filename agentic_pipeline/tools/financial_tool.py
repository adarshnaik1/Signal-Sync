#import yfinance as yf


#def fetch_company_data(ticker):

    #stock = yf.Ticker(ticker)

    #info = stock.info

    #financials = stock.financials
    #balance_sheet = stock.balance_sheet
    #cashflow = stock.cashflow

    #return {
        #"info": info,
        #"financials": financials,
        #"balance_sheet": balance_sheet,
        #"cashflow": cashflow
    #}



import yfinance as yf

#import contextlib
#import io


def fetch_company_data(ticker, exchange):

    try:

        exchange = exchange.upper()

        # Add Yahoo Finance suffix
        if exchange == "NSE":
            ticker = ticker + ".NS"

        elif exchange == "BSE":
            ticker = ticker + ".BO"

        else:
            raise ValueError("Exchange must be either NSE or BSE.")

        #with contextlib.redirect_stdout(io.StringIO()), \
        #contextlib.redirect_stderr(io.StringIO()):               --> To suppress HTTP warnings from yfinance, but it also suppresses our own error messages, so commenting out for now.

        stock = yf.Ticker(ticker)

        info = stock.info

        # Invalid ticker check
        if not info or "symbol" not in info:
            raise ValueError("Invalid ticker symbol.")

        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow
        history = stock.history(period="2y")

        return {
            "info": info,
            "financials": financials,
            "balance_sheet": balance_sheet,
            "cashflow": cashflow,
            "history": history
        }

    except ValueError as ve:
        print(f"Validation Error: {ve}")
        return None

    except Exception as e:
        print(f"Error fetching company data: {e}")
        return None