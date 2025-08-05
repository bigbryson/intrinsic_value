# django_stock_screener_materio/apps/screener_app/data_services.py
import os
import pandas as pd
import yfinance as yf
import numpy as np
from django.conf import settings
import logging
from datetime import datetime, timedelta
from django.core.cache import cache
import finnhub
from django.conf import settings


logger = logging.getLogger(__name__)

# --- Helper Function to get CSV paths from settings ---
def get_csv_file_path(config_key):
    base_path = getattr(settings, 'DOLT_EARNINGS_DATA_PATH', None)
    filenames = getattr(settings, 'DOLTHUB_FILENAMES_CONFIG', {})
    if not base_path or config_key not in filenames:
        logger.error(f"Config for '{config_key}' not found in settings.py.")
        return None
    path = os.path.join(base_path, filenames[config_key])
    if not os.path.exists(path):
        logger.warning(f"CSV file not found: {path}. Run 'python manage.py sync_dolt_csvs'.")
        return None
    return path

# --- Main CSV Loading and Filtering Function (Corrected Definition) ---
def load_csv_data(config_key, usecols=None, filter_annual=False):
    file_path = get_csv_file_path(config_key)
    if not file_path: return pd.DataFrame()
    try:
        df = pd.read_csv(file_path, usecols=usecols)

        # Filter for Annual Data if requested and possible
        if filter_annual and 'period' in df.columns:
            annual_indicator = getattr(settings, 'ANNUAL_REPORT_PERIOD_INDICATOR', 'Year')
            df = df[df['period'] == annual_indicator].copy()
            if df.empty:
                logger.warning(f"Filtering for period='{annual_indicator}' resulted in an empty DataFrame for {config_key}.")

        # Standardize common column names for consistent use
        rename_map = {'act_symbol': 'symbol', 'period_end_date': 'date'}
        df.rename(columns=rename_map, inplace=True, errors='ignore')

        if 'date' in df.columns:
             df['date'] = pd.to_datetime(df['date'], errors='coerce')

        return df
    except Exception as e:
        logger.error(f"Error loading CSV {file_path}: {e}")
        return pd.DataFrame()


# --- yfinance Data Fetching Functions ---
def get_yfinance_supplemental_data(symbol_ticker):
    try:
        info = yf.Ticker(symbol_ticker).info
        return {'company_name': info.get('longName', symbol_ticker), 'prev_close': info.get('previousClose')}
    except:
        return {'company_name': symbol_ticker, 'prev_close': None}

def get_yfinance_historical_prices(symbol_ticker, period="5y"):
    try: return yf.Ticker(symbol_ticker).history(period=period)
    except: return pd.DataFrame()

# --- Calculation Functions (Defined Before They Are Called) ---

def get_latest_annual_eps(df_cash_flow_annual, symbol_ticker):
    if df_cash_flow_annual.empty: return None
    symbol_data = df_cash_flow_annual[df_cash_flow_annual['symbol'] == symbol_ticker].sort_values(by='date', ascending=False)
    if not symbol_data.empty:
        return pd.to_numeric(symbol_data['diluted_net_eps'].iloc[0], errors='coerce')
    return None

def calculate_avg_pe_5yr(symbol_ticker, latest_annual_eps):
    if latest_annual_eps is None or latest_annual_eps == 0: return None
    hist_prices = get_yfinance_historical_prices(symbol_ticker)
    if hist_prices.empty: return None
    try:
        pe_series = hist_prices['Close'] / latest_annual_eps
        return round(pe_series.mean(), 2)
    except: return None

def get_latest_bvps(df_equity_annual, symbol_ticker):
    if df_equity_annual.empty: return None
    equity_info = df_equity_annual[df_equity_annual['symbol'] == symbol_ticker].sort_values('date', ascending=False)
    if equity_info.empty: return None
    try:
        total_equity = pd.to_numeric(equity_info['total_equity'].iloc[0], errors='coerce')
        shares_out = pd.to_numeric(equity_info['shares_outstanding'].iloc[0], errors='coerce')
        if pd.notna(total_equity) and pd.notna(shares_out) and shares_out != 0:
            return round(total_equity / shares_out, 2)
    except: return None
    return None

def calculate_graham_number(annual_eps, bvps):
    if annual_eps is None or bvps is None or annual_eps <= 0 or bvps <= 0: return None
    try: return round(np.sqrt(22.5 * annual_eps * bvps), 2)
    except: return None

def calculate_cagr(series_data):
    if not isinstance(series_data, pd.Series) or len(series_data) < 2: return None
    num_years = len(series_data) - 1
    if num_years == 0: return None
    start_val, end_val = series_data.iloc[0], series_data.iloc[-1]
    if start_val == 0: return None
    if (start_val < 0 and end_val > 0) or (start_val > 0 and end_val < 0) or (start_val <0 and end_val <0): return "N/A (Complex)"
    try: return round(((end_val / start_val) ** (1 / num_years) - 1) * 100, 2)
    except: return None

def calculate_eps_growth_rate(df_eps_hist, symbol_ticker, years=10):
    if df_eps_hist.empty: return None
    symbol_data = df_eps_hist[df_eps_hist['symbol'] == symbol_ticker].copy()
    if symbol_data.empty: return None
    try:
        symbol_data.loc[:, 'reported'] = pd.to_numeric(symbol_data['reported'], errors='coerce')
        annual_eps = symbol_data.set_index('date')['reported'].resample('YE').sum().dropna()
        if len(annual_eps) < 2: return None
        years_for_growth = min(years, len(annual_eps) - 1)
        if years_for_growth <= 0: return None
        return calculate_cagr(annual_eps.tail(years_for_growth + 1))
    except Exception as e:
        logger.error(f"Error in calculate_eps_growth_rate for {symbol_ticker}: {e}")
    return None

def calculate_eps_avg(df_eps_hist, symbol_ticker, years=5):
    if df_eps_hist.empty: return None
    symbol_data = df_eps_hist[df_eps_hist['symbol'] == symbol_ticker].copy()
    if symbol_data.empty: return None
    try:
        symbol_data.loc[:, 'reported'] = pd.to_numeric(symbol_data['reported'], errors='coerce')
        annual_eps = symbol_data.set_index('date')['reported'].resample('YE').sum().dropna()
        return round(annual_eps.tail(years).mean(), 2) if not annual_eps.empty else None
    except: return None

def calculate_intrinsic_value(annual_eps, growth_rate_pct):
    aaa_yield = getattr(settings, 'CURRENT_AAA_BOND_YIELD', 4.5)
    if annual_eps is None or annual_eps <= 0 or growth_rate_pct is None or not isinstance(growth_rate_pct, (int, float)): return None
    try: return round((annual_eps * (7 + growth_rate_pct) * 4.4) / aaa_yield, 2)
    except: return None

# In django_stock_screener_materio/apps/screener_app/data_services.py

# ... (keep all your existing functions: load_csv_data, get_screener_data, etc.) ...


# ---  FUNCTION FOR THE DETAIL PAGE ---
def calculate_historical_returns(symbol_ticker):
    """Fetches 10 years of price data and calculates YTD, 3, 5, and 10-year returns."""
    try:
        hist = yf.Ticker(symbol_ticker).history(period="10y", auto_adjust=True)
        if hist.empty:
            return {}

        returns = {}
        today = hist.index[-1]

        # --- YTD Return ---
        start_of_year_date = hist.loc[f'{today.year}-01-01':].index.min()
        if pd.notna(start_of_year_date):
            price_start_ytd = hist.loc[start_of_year_date, 'Close']
            price_end_ytd = hist.loc[today, 'Close']
            if price_start_ytd != 0:
                returns['ytd'] = round(((price_end_ytd / price_start_ytd) - 1) * 100, 2)

        # --- 3, 5, 10-Year Annualized Returns (CAGR) ---
        for year in [3, 5, 10]:
            start_date = today - pd.DateOffset(years=year)
            actual_start_date = hist.index.asof(start_date)

            if pd.notna(actual_start_date):
                price_start = hist.loc[actual_start_date, 'Close']
                price_end = hist.loc[today, 'Close']
                num_years = (today - actual_start_date).days / 365.25
                if price_start > 0 and num_years > 0:
                    cagr = ((price_end / price_start) ** (1 / num_years)) - 1
                    returns[f'{year}y'] = round(cagr * 100, 2)

        return returns
    except Exception as e:
        logger.error(f"Failed to calculate historical returns for {symbol_ticker}: {e}")
        return {}


# --- Main Function for Stock Detail Page ---
def get_stock_detail_data(symbol_ticker):
    """
    Fetches all necessary in-depth data for a single stock for its detail page.
    """
    logger.info(f"Fetching ALL detail data for symbol: {symbol_ticker}")

    # Dictionaries to hold all the data we gather
    profile_data = {}
    chart_data = {}
    key_stats = {}
    returns_data = {}
    financials = {}
    calculations = {}

    # --- Part 1: Fetch all real-time and profile data from yfinance ---
    try:
        ticker = yf.Ticker(symbol_ticker)
        info = ticker.info

        # Section 1a: Get Company Profile data
        profile_data = {
            'longName': info.get('longName', symbol_ticker),
            'symbol': info.get('symbol'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'website': info.get('website', '#'),
            'longBusinessSummary': info.get('longBusinessSummary', 'No summary available.'),
        }

        # Section 1b: Get Data for Stock Chart (1 year)
        hist_chart = ticker.history(period="1y")
        if not hist_chart.empty:
            chart_data = {
                'dates': [d.strftime('%Y-%m-%d') for d in hist_chart.index],
                'prices': [round(p, 2) for p in hist_chart['Close']],
            }

        # Section 1c: Get Key Statistics
        key_stats = {
            "Previous Close": info.get('previousClose'),
            "Open": info.get('open'),
            "Bid": f"{info.get('bid', 0)} x {info.get('bidSize', 0)}",
            "Ask": f"{info.get('ask', 0)} x {info.get('askSize', 0)}",
            "Day's Range": f"{info.get('dayLow', 'N/A')} - {info.get('dayHigh', 'N/A')}",
            "52 Week Range": f"{info.get('fiftyTwoWeekLow', 'N/A')} - {info.get('fiftyTwoWeekHigh', 'N/A')}",
            "Volume": f"{info.get('volume', 0):,}", # Format with commas
            "Avg. Volume": f"{info.get('averageVolume', 0):,}", # Format with commas
            "Market Cap (intraday)": f"{info.get('marketCap', 0):,}", # Format with commas
            "Beta (5Y Monthly)": info.get('beta'),
            "PE Ratio (TTM)": info.get('trailingPE'),
            "EPS (TTM)": info.get('trailingEps'),
            "Earnings Date": datetime.fromtimestamp(info['earningsTimestamp']).strftime('%Y-%m-%d') if 'earningsTimestamp' in info else 'N/A',
            "Forward Dividend & Yield": f"{info.get('dividendRate', 'N/A')} ({info.get('dividendYield', 0) * 100:.2f}%)" if 'dividendYield' in info and info.get('dividendYield') else 'N/A',
            "Ex-Dividend Date": datetime.fromtimestamp(info['exDividendDate']).strftime('%Y-%m-%d') if 'exDividendDate' in info else 'N/A',
            "1y Target Est": info.get('targetMeanPrice'),
        }

    except Exception as e:
        logger.error(f"yfinance fetch failed for detail page of {symbol_ticker}: {e}")
        profile_data['longName'] = f"{symbol_ticker} (Live data unavailable)"


    # --- Part 2: Calculate Historical Returns ---
    returns_data = calculate_historical_returns(symbol_ticker)


    # --- Part 3: Get Financial Statements from Local CSVs ---
    # (This logic can be expanded to show more detailed tables later)
    df_income = load_csv_data('income_statement')
    if not df_income.empty:
        symbol_income = df_income[df_income['symbol'] == symbol_ticker].sort_values('date', ascending=False)
        financials['income_statement'] = symbol_income.to_dict('records')


    # --- Part 4: Perform Graham and Intrinsic Value Calculations ---
    # Load necessary dataframes for the single symbol
    df_cash_flow_annual = load_csv_data('cash_flow', usecols=['act_symbol', 'date', 'period', 'diluted_net_eps'], filter_annual=True)
    df_equity_annual = load_csv_data('equity', usecols=['act_symbol', 'date', 'period', 'total_equity', 'shares_outstanding'], filter_annual=True)
    df_eps_history = load_csv_data('eps_history', usecols=['act_symbol', 'period_end_date', 'reported'])

    # Perform calculations by calling the helpers we already built
    latest_annual_eps = get_latest_annual_eps(df_cash_flow_annual, symbol_ticker)
    bvps = get_latest_bvps(df_equity_annual, symbol_ticker)
    eps_growth = calculate_eps_growth_rate(df_eps_history, symbol_ticker)

    graham_num = calculate_graham_number(latest_annual_eps, bvps)
    intrinsic_val = calculate_intrinsic_value(latest_annual_eps, eps_growth)

    calculations = {
        'graham_number': graham_num,
        'intrinsic_value': intrinsic_val
    }

    # --- Part 5: Combine all data into a single dictionary ---
    return {
        'profile': profile_data,
        'chart_data': chart_data,
        'key_stats': key_stats,
        'returns_data': returns_data,
        'financials': financials,
        'calculations': calculations,
    }


    # Save the combined data to the cache for 1 hour (3600 seconds)
   # cache.set(cache_key, final_data, 3600)

    #return final_data

# --- NEW High-Performance Main Orchestrating Function ---
def get_screener_data_for_symbols(symbols_to_process):
    if not symbols_to_process:
        return []

    logger.info(f"--- Starting data processing for {len(symbols_to_process)} symbols for current page ---")

    # Load dataframes only when this function is called
    df_cash_flow_annual = load_csv_data('cash_flow', usecols=['act_symbol', 'date', 'period', 'diluted_net_eps'], filter_annual=True)
    df_equity_annual = load_csv_data('equity', usecols=['act_symbol', 'date', 'period', 'total_equity', 'shares_outstanding'], filter_annual=True)
    df_eps_history = load_csv_data('eps_history', usecols=['act_symbol', 'period_end_date', 'reported'])

    all_processed_data = []
    for symbol in symbols_to_process:
        # The full calculation loop from our previous version goes here
        # This logic is now only performed for the stocks on the current page
        yf_data = get_yfinance_supplemental_data(symbol)
        prev_close = yf_data.get('prev_close')

        latest_annual_eps = get_latest_annual_eps(df_cash_flow_annual, symbol)
        avg_pe = calculate_avg_pe_5yr(symbol, latest_annual_eps)
        bvps = get_latest_bvps(df_equity_annual, symbol)
        graham_num = calculate_graham_number(latest_annual_eps, bvps)
        eps_growth = calculate_eps_growth_rate(df_eps_history, symbol)
        eps_avg_5yr = calculate_eps_avg(df_eps_history, symbol, years=5)
        intrinsic_val = calculate_intrinsic_value(latest_annual_eps, eps_growth)

        # ... (graham_diff and intrinsic_diff calculations) ...
        graham_diff = round(((prev_close - graham_num) / graham_num) * 100, 2) if prev_close and graham_num and graham_num != 0 else None
        intrinsic_diff = round(((prev_close - intrinsic_val) / intrinsic_val) * 100, 2) if prev_close and intrinsic_val and intrinsic_val != 0 else None

        all_processed_data.append({
            "Company Name": yf_data.get('company_name', symbol),
            "Symbol": symbol.upper(),
            "Prev. Close": prev_close,
            "Avg P/E (5yr)": avg_pe,
            "Graham Num": graham_num,
            "Graham Diff %": f"{graham_diff}%" if graham_diff is not None else "N/A",
            "Intrinsic Val": intrinsic_val,
            "Intrinsic Diff %": f"{intrinsic_diff}%" if intrinsic_diff is not None else "N/A",
            "EPS AVG (5yr)": eps_avg_5yr,
            "Growth Rate (avg past 10 yrs)": f"{eps_growth}%" if isinstance(eps_growth, (int,float)) else eps_growth if eps_growth else "N/A",
        })

    return all_processed_data
