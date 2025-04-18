import requests
import json
import pandas as pd
import numpy as np
from django.conf import settings
import os
from dotenv import load_dotenv
from .angel_one import AngelOneAPI
from datetime import datetime, timedelta

# Load environment variables
load_dotenv(override=True)

def get_historical_data(symbol, interval="5min", limit=100):
    """
    Get historical price data for a given symbol using Angel One API
    
    Parameters:
    symbol (str): The trading symbol (e.g., 'RELIANCE')
    interval (str): Time interval (e.g., '1min', '5min', '15min', '4h', '1day', '1week')
    limit (int): Number of data points to retrieve
    
    Returns:
    pandas.DataFrame: DataFrame with OHLCV data or None if the request fails
    """
    try:
        # Initialize Angel One API
        api = AngelOneAPI()
        
        # Connect to API
        if not api.connect():
            print(f"Failed to connect to Angel One API for {symbol}")
            return generate_mock_data(symbol, interval, limit)
        
        # Get current date and date 30 days ago (or appropriate time range based on interval)
        to_date = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
        
        if interval == '1min' or interval == '5min' or interval == '15min':
            # For smaller intervals, get less historical data
            from_date = (pd.Timestamp.now() - pd.Timedelta(days=5)).strftime('%Y-%m-%d %H:%M')
        else:
            # For larger intervals, get more historical data
            from_date = (pd.Timestamp.now() - pd.Timedelta(days=60)).strftime('%Y-%m-%d %H:%M')
            
        # Map interval to Angel One format
        angel_interval = interval
        if interval == '4h':
            angel_interval = 'ONE_HOUR'  # Use 1 hour and resample later
        elif interval == '1day':
            angel_interval = 'ONE_DAY'
        elif interval == '1week':
            angel_interval = 'ONE_WEEK'
        
        # Get exchange (default to NSE)
        exchange = 'NSE'
        
        # Fetch historical data
        df = api.get_historical_data(
            symbol=symbol,
            exchange=exchange,
            interval=angel_interval,
            from_date=from_date,
            to_date=to_date
        )
        
        if df is not None and not df.empty:
            # Resample to 4h if needed
            if interval == '4h' and angel_interval == 'ONE_HOUR':
                df = df.resample('4H').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna().reset_index()
            
            # Add technical indicators
            df = api.add_indicators(df)
            
            # Limit the number of returned records
            if limit and len(df) > limit:
                df = df.tail(limit)
                
            return df
        else:
            print(f"No data returned from Angel One API for {symbol}")
            return generate_mock_data(symbol, interval, limit)
            
    except Exception as e:
        print(f"Error fetching historical data for {symbol}: {str(e)}")
        return generate_mock_data(symbol, interval, limit)

def generate_mock_data(symbol, interval="5min", limit=100):
    """Generate mock historical data for development purposes"""
    print(f"Generating mock data for {symbol} with {interval} interval")
    
    # Create a date range for the timestamps
    end_date = pd.Timestamp.now()
    
    if interval == "1min":
        freq = "T"  # minute frequency
    elif interval == "5min":
        freq = "5T"
    elif interval == "15min":
        freq = "15T"
    elif interval == "30min":
        freq = "30T"
    elif interval == "60min" or interval == "1h":
        freq = "H"
    elif interval == "4h":
        freq = "4H"
    elif interval == "1day":
        freq = "D"
    elif interval == "1week":
        freq = "W"
    else:
        freq = "D"
    
    # Generate timestamps
    timestamps = pd.date_range(end=end_date, periods=limit, freq=freq)
    
    # Base price between 50-500
    base_price = np.random.uniform(50, 500)
    
    # Generate random price movements
    prices = np.random.normal(0, 1, size=limit).cumsum() * (base_price * 0.01) + base_price
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': prices,
        'close': prices * np.random.uniform(0.98, 1.02, size=limit),
        'high': prices * np.random.uniform(1.01, 1.05, size=limit),
        'low': prices * np.random.uniform(0.95, 0.99, size=limit),
        'volume': np.random.randint(1000, 100000, size=limit)
    })
    
    return df

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




