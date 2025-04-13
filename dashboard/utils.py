import requests
import json
import pandas as pd
import numpy as np
from django.conf import settings

ALPHA_VANTAGE_API_KEY = "SEFXT3DC8C92Z878"

def get_historical_data(symbol, interval="5min", limit=100):
    """
    Get historical price data for a given symbol using Alpha Vantage API
    
    Parameters:
    symbol (str): The trading symbol (e.g., 'MSFT')
    interval (str): Time interval (e.g., '1min', '5min', '15min', '4h', '1day', '1week')
    limit (int): Number of data points to retrieve
    
    Returns:
    pandas.DataFrame: DataFrame with OHLCV data or None if the request fails
    """
    # Map our timeframe to Alpha Vantage format
    av_function = "TIME_SERIES_INTRADAY"
    av_interval = interval
    
    if interval in ["1min", "5min", "15min"]:
        av_function = "TIME_SERIES_INTRADAY"
    elif interval == "4h":
        # Alpha Vantage doesn't have 4h directly, use daily and resample later
        av_function = "TIME_SERIES_DAILY"
        av_interval = None
    elif interval == "1day":
        av_function = "TIME_SERIES_DAILY"
        av_interval = None
    elif interval == "1week":
        av_function = "TIME_SERIES_WEEKLY"
        av_interval = None
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": av_function,
        "symbol": symbol,
        "outputsize": "full",
        "apikey": ALPHA_VANTAGE_API_KEY,
    }
    
    # Add interval parameter only for intraday data
    if av_interval:
        params["interval"] = av_interval
    
    response = requests.get(url, params=params)
    data = response.json()
    
    try:
        # Get the appropriate time series key based on the function
        if av_function == "TIME_SERIES_INTRADAY":
            time_series_key = f"Time Series ({interval})"
        elif av_function == "TIME_SERIES_DAILY":
            time_series_key = "Time Series (Daily)"
        elif av_function == "TIME_SERIES_WEEKLY":
            time_series_key = "Weekly Time Series"
        else:
            time_series_key = None
            
        if not time_series_key or time_series_key not in data:
            print(f"Error: Invalid time series key for {symbol} with interval {interval}")
            return None
            
        time_series = data[time_series_key]
        
        # Convert to DataFrame
        ohlcv_data = []
        for date_str, values in time_series.items():
            ohlcv_data.append({
                'timestamp': date_str,
                'open': float(values['1. open']),
                'high': float(values['2. high']),
                'low': float(values['3. low']),
                'close': float(values['4. close']),
                'volume': float(values['5. volume']) if '5. volume' in values else 0
            })
        
        # Create DataFrame and sort by timestamp
        df = pd.DataFrame(ohlcv_data)
        df = df.sort_values('timestamp')
        
        # Special handling for 4h interval - resample from daily data
        if interval == "4h" and not df.empty:
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # Set timestamp as index
            df = df.set_index('timestamp')
            # Resample to 4h by forward fill
            df = df.resample('4H').ffill().reset_index()
        
        # Limit the number of returned records
        if limit and len(df) > limit:
            df = df.tail(limit)
        
        return df
    except (KeyError, ValueError) as e:
        print(f"Error processing data for {symbol} with interval {interval}: {e}")
        return None

def get_stock_price(symbol, interval="5min"):
    """Get the latest price for a stock"""
    df = get_historical_data(symbol, interval, limit=1)
    if df is not None and not df.empty:
        return df.iloc[0]['close']
    return None

# Indicator calculation functions
def calculate_sma(data, period):
    """Calculate Simple Moving Average"""
    return data.rolling(window=period).mean()

def calculate_ema(data, period):
    """Calculate Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()

def calculate_rsi(data, period=14):
    """Calculate Relative Strength Index"""
    # Calculate price changes
    delta = data.diff()
    
    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Calculate average gain and loss
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # Calculate RS
    rs = avg_gain / avg_loss
    
    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    ema_fast = calculate_ema(data, fast_period)
    ema_slow = calculate_ema(data, slow_period)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_indicator(df, indicator_name, params):
    """Calculate an indicator based on its name and parameters"""
    if df is None or df.empty:
        return None
    
    # Parse JSON parameters if it's a string
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            params = {}
    
    # Get close prices
    close_prices = df['close']
    
    # Calculate the appropriate indicator
    if indicator_name == 'SMA':
        period = params.get('period', 14)
        result = calculate_sma(close_prices, period)
    elif indicator_name == 'EMA':
        period = params.get('period', 14)
        result = calculate_ema(close_prices, period)
    elif indicator_name == 'RSI':
        period = params.get('period', 14)
        result = calculate_rsi(close_prices, period)
    elif indicator_name == 'MACD':
        fast_period = params.get('fast_period', 12)
        slow_period = params.get('slow_period', 26)
        signal_period = params.get('signal_period', 9)
        macd_line, signal_line, histogram = calculate_macd(
            close_prices, fast_period, slow_period, signal_period
        )
        # Return the MACD line by default
        result = macd_line
    else:
        return None
    
    # Return the latest value
    if not result.empty:
        return result.iloc[-1]
    
    return None

def check_crossover(indicator1_value, indicator2_value, condition):
    """Check if a crossover condition is met"""
    if indicator1_value is None or indicator2_value is None:
        return False
    
    if condition == 'above':
        return indicator1_value > indicator2_value
    elif condition == 'below':
        return indicator1_value < indicator2_value
    elif condition == 'equals':
        return indicator1_value == indicator2_value
    
    return False




