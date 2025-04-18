from SmartApi import SmartConnect
import os
from dotenv import load_dotenv
# Load environment variables from .env file, overriding existing ones
load_dotenv(override=True)

import pandas as pd
from datetime import datetime, timedelta
import requests
import json
import ta  # Technical analysis library for indicators
import time
import random


class AngelOneAPI:
    def __init__(self):
        self.api_key = os.getenv('ANGEL_API_KEY')
        self.client_id = os.getenv('ANGEL_CLIENT_ID')
        self.password = os.getenv('ANGEL_PASSWORD')
        self.token = os.getenv('ANGEL_TOKEN')
        self.client_local_ip = os.getenv('CLIENT_LOCAL_IP', '192.168.56.1')
        self.client_public_ip = os.getenv('CLIENT_PUBLIC_IP', '43.241.193.61')
        self.mac_address = os.getenv('MAC_ADDRESS', 'C0-35-32-51-AA-3B')
        self.smart_api = None
        self.base_url = "https://apiconnect.angelone.in"
        self.retry_count = 3
        self.retry_delay = 2  # seconds between retries
        
    def connect(self):
        """Initialize connection to Angel One API with retry logic"""
        for attempt in range(self.retry_count):
            try:
                self.smart_api = SmartConnect(
                    api_key=self.api_key,
                    access_token=self.token,
                    userId=self.client_id,
                    clientLocalIP=self.client_local_ip,
                    clientPublicIP=self.client_public_ip,
                    clientMacAddress=self.mac_address
                )
                
                # Test connection by getting profile
                profile = self.smart_api.getProfile()
                if profile.get('status'):
                    print(f"Successfully connected to Angel One API for user {profile.get('data', {}).get('name', 'Unknown')}")
                    return True
                else:
                    error_msg = profile.get('message', 'Unknown error')
                    print(f"Connection error: {error_msg}")
                    
                    # Check if token expired
                    if 'token' in error_msg.lower() or 'expired' in error_msg.lower():
                        print("Token may have expired. Please get a new token.")
                        return False
                        
            except Exception as e:
                print(f"Attempt {attempt+1}: Error connecting to Angel One API: {str(e)}")
                
            # Wait before retrying
            if attempt < self.retry_count - 1:
                delay = self.retry_delay * (attempt + 1) + random.uniform(0.1, 1.0)
                print(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                
        print(f"Failed to connect after {self.retry_count} attempts.")
        return False
    
    def get_headers(self):
        """Get headers for API requests"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-ClientLocalIP": self.client_local_ip,
            "X-ClientPublicIP": self.client_public_ip,
            "X-MACAddress": self.mac_address,
            "X-PrivateKey": self.api_key,
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "Authorization": f"Bearer {self.token}"
        }
            
    def get_quote(self, exchange, symbol_token):
        """Get quote for a symbol using REST API with retry logic"""
        for attempt in range(self.retry_count):
            try:
                endpoint = "/rest/secure/angelbroking/market/v1/quote/"
                payload = {
                    "mode": "FULL",
                    "exchangeTokens": {
                        exchange: [symbol_token]
                    }
                }
                
                headers = self.get_headers()
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    print("Rate limit exceeded. Waiting before retry...")
                else:
                    print(f"Error fetching quote: {response.status_code}, {response.text}")
                    
            except Exception as e:
                print(f"Attempt {attempt+1}: Error fetching quote: {str(e)}")
                
            # Wait before retrying with exponential backoff
            if attempt < self.retry_count - 1:
                delay = self.retry_delay * (2 ** attempt) + random.uniform(0.1, 1.0)
                print(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                
        return None
            
    def get_historical_data(self, symbol, exchange, interval, from_date, to_date):
        """Get historical data for a symbol with improved error handling"""
        for attempt in range(self.retry_count):
            try:
                if not self.smart_api:
                    if not self.connect():
                        return None
                        
                params = {
                    "exchange": exchange,
                    "symboltoken": symbol,
                    "interval": interval,
                    "fromdate": from_date,
                    "todate": to_date
                }
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.5 + random.uniform(0, 0.5))
                
                data = self.smart_api.getCandleData(params)
                
                # Convert to pandas DataFrame
                df = pd.DataFrame(data)
                if not df.empty:
                    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    
                    # Add technical indicators
                    self.add_indicators(df)
                    return df
                    
            except Exception as e:
                # Check for rate limit
                if "rate" in str(e).lower() or "access denied" in str(e).lower():
                    print(f"Rate limit exceeded. Waiting before retry...")
                else:
                    print(f"Attempt {attempt+1}: Error fetching historical data: {str(e)}")
                
            # Wait before retrying with exponential backoff
            if attempt < self.retry_count - 1:
                delay = self.retry_delay * (2 ** attempt) + random.uniform(0.5, 2.0)
                print(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                
        print(f"Failed to get historical data for {symbol} after {self.retry_count} attempts.")
        return None
    
    def add_indicators(self, dataframe):
        """Add technical indicators to the dataframe"""
        if dataframe is None or dataframe.empty:
            return None
        
        # Add RSI (Relative Strength Index)
        dataframe['rsi'] = ta.momentum.RSIIndicator(dataframe['close']).rsi()
        
        # Add MACD (Moving Average Convergence Divergence)
        macd = ta.trend.MACD(dataframe['close'])
        dataframe['macd'] = macd.macd()
        dataframe['macd_signal'] = macd.macd_signal()
        dataframe['macd_histogram'] = macd.macd_diff()
        
        # Add Bollinger Bands
        bollinger = ta.volatility.BollingerBands(dataframe['close'])
        dataframe['bollinger_high'] = bollinger.bollinger_hband()
        dataframe['bollinger_low'] = bollinger.bollinger_lband()
        dataframe['bollinger_mid'] = bollinger.bollinger_mavg()
        
        # Add Moving Averages
        dataframe['sma_20'] = ta.trend.SMAIndicator(dataframe['close'], window=20).sma_indicator()
        dataframe['sma_50'] = ta.trend.SMAIndicator(dataframe['close'], window=50).sma_indicator()
        dataframe['sma_200'] = ta.trend.SMAIndicator(dataframe['close'], window=200).sma_indicator()
        
        # Add ATR (Average True Range)
        dataframe['atr'] = ta.volatility.AverageTrueRange(dataframe['high'], dataframe['low'], dataframe['close']).average_true_range()
        
        return dataframe
            
    def check_alerts(self, dataframe, symbol, conditions):
        """Check if any alert conditions are met"""
        if dataframe is None or dataframe.empty:
            return []
            
        alerts = []
        latest = dataframe.iloc[-1]
        
        # Example conditions (customize based on your requirements)
        if 'rsi_overbought' in conditions and latest['rsi'] > conditions['rsi_overbought']:
            alerts.append(f"{symbol}: RSI Overbought ({latest['rsi']:.2f})")
            
        if 'rsi_oversold' in conditions and latest['rsi'] < conditions['rsi_oversold']:
            alerts.append(f"{symbol}: RSI Oversold ({latest['rsi']:.2f})")
        
        if 'macd_crossover' in conditions and conditions['macd_crossover']:
            # Check if MACD line crosses above signal line
            if dataframe['macd'].iloc[-2] < dataframe['macd_signal'].iloc[-2] and \
               latest['macd'] > latest['macd_signal']:
                alerts.append(f"{symbol}: MACD Bullish Crossover")
                
        if 'macd_crossunder' in conditions and conditions['macd_crossunder']:
            # Check if MACD line crosses below signal line
            if dataframe['macd'].iloc[-2] > dataframe['macd_signal'].iloc[-2] and \
               latest['macd'] < latest['macd_signal']:
                alerts.append(f"{symbol}: MACD Bearish Crossunder")
        
        if 'price_above_sma' in conditions and latest['close'] > latest['sma_' + str(conditions['price_above_sma'])]:
            alerts.append(f"{symbol}: Price Above SMA{conditions['price_above_sma']}")
            
        if 'price_below_sma' in conditions and latest['close'] < latest['sma_' + str(conditions['price_below_sma'])]:
            alerts.append(f"{symbol}: Price Below SMA{conditions['price_below_sma']}")
            
        if 'bollinger_breakout_up' in conditions and conditions['bollinger_breakout_up']:
            if latest['close'] > latest['bollinger_high']:
                alerts.append(f"{symbol}: Bollinger Band Upper Breakout")
                
        if 'bollinger_breakout_down' in conditions and conditions['bollinger_breakout_down']:
            if latest['close'] < latest['bollinger_low']:
                alerts.append(f"{symbol}: Bollinger Band Lower Breakout")
                
        return alerts
        
    def get_ltp(self, symbol, exchange):
        """Get Last Traded Price for a symbol"""
        try:
            if not self.smart_api:
                if not self.connect():
                    return None
                    
            ltp_data = self.smart_api.ltpData(exchange, symbol, symbol)
            return ltp_data['ltp']
            
        except Exception as e:
            print(f"Error fetching LTP: {str(e)}")
            return None
            
    def place_order(self, symbol, exchange, quantity, buy_sell, order_type='MARKET'):
        """Place an order"""
        try:
            if not self.smart_api:
                if not self.connect():
                    return None
                    
            order_params = {
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": symbol,
                "transactiontype": buy_sell,
                "quantity": quantity,
                "producttype": "INTRADAY",
                "ordertype": order_type,
                "exchange": exchange,
                "validity": "DAY",
                "disclosedquantity": "0",
                "price": "0",
                "triggerprice": "0"
            }
            
            order_id = self.smart_api.placeOrder(order_params)
            return order_id
            
        except Exception as e:
            print(f"Error placing order: {str(e)}")
            return None 