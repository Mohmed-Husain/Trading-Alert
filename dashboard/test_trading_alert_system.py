from angel_one import AngelOneAPI
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
import os
import time

class TradingAlertSystem:
    def __init__(self):
        self.api = AngelOneAPI()
        self.symbols = [
            {"symbol": "RELIANCE", "token": "2885", "exchange": "NSE"},
            {"symbol": "INFY", "token": "1594", "exchange": "NSE"},
            {"symbol": "HDFCBANK", "token": "1333", "exchange": "NSE"},
            {"symbol": "TCS", "token": "11536", "exchange": "NSE"},
            {"symbol": "TATASTEEL", "token": "3499", "exchange": "NSE"}
        ]
        
        # Alert conditions
        self.alert_conditions = {
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "macd_crossover": True,
            "macd_crossunder": True,
            "price_above_sma": 50,
            "price_below_sma": 20,
            "bollinger_breakout_up": True,
            "bollinger_breakout_down": True
        }
        
        # Create output directory
        os.makedirs("data", exist_ok=True)
        
    def fetch_quotes(self):
        """Fetch real-time quotes for all symbols"""
        print("\n=== FETCHING REAL-TIME QUOTES ===")
        
        quotes_data = {}
        for symbol_info in self.symbols:
            symbol = symbol_info["symbol"]
            exchange = symbol_info["exchange"]
            token = symbol_info["token"]
            
            print(f"Fetching quote for {symbol}...")
            quote = self.api.get_quote(exchange, token)
            
            if quote and quote.get('status') and quote.get('message') == "SUCCESS":
                # Correct format: data -> fetched -> array of fetched symbols
                fetched_data = quote.get('data', {}).get('fetched', [])
                if fetched_data and len(fetched_data) > 0:
                    symbol_data = fetched_data[0]  # Get the first symbol data
                    quotes_data[symbol] = {
                        "ltp": symbol_data.get('ltp'),
                        "open": symbol_data.get('open'),
                        "high": symbol_data.get('high'),
                        "low": symbol_data.get('low'),
                        "close": symbol_data.get('close'),
                        "volume": symbol_data.get('tradeVolume'),
                        "timestamp": symbol_data.get('exchTradeTime'),
                        "change": symbol_data.get('netChange'),
                        "change_percent": symbol_data.get('percentChange')
                    }
                    print(f"  ✓ {symbol}: ₹{symbol_data.get('ltp')} ({symbol_data.get('percentChange')}%)")
                else:
                    print(f"  ✗ {symbol}: No data found")
            else:
                print(f"  ✗ {symbol}: Error fetching quote")
                
        return quotes_data
    
    def fetch_historical_data(self, symbol_info, days=30):
        """Fetch historical data for a symbol"""
        symbol = symbol_info["symbol"]
        exchange = symbol_info["exchange"]
        token = symbol_info["token"]
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        to_date = end_date.strftime('%Y-%m-%d %H:%M')
        from_date = start_date.strftime('%Y-%m-%d %H:%M')
        
        print(f"Fetching historical data for {symbol} ({from_date} to {to_date})...")
        
        try:
            # Make direct REST API call for historical data
            endpoint = "/rest/secure/angelbroking/historical/v1/getCandleData"
            payload = {
                "exchange": exchange,
                "symboltoken": token,
                "interval": "ONE_DAY",
                "fromdate": from_date,
                "todate": to_date
            }
            
            headers = self.api.get_headers()
            url = f"{self.api.base_url}{endpoint}"
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') and data.get('data'):
                    candle_data = data.get('data', [])
                    if candle_data and len(candle_data) > 0:
                        # Create DataFrame from candle data
                        df = pd.DataFrame(candle_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        df.set_index('timestamp', inplace=True)
                        
                        # Convert columns to numeric
                        for col in ['open', 'high', 'low', 'close', 'volume']:
                            df[col] = pd.to_numeric(df[col])
                        
                        # Save raw data
                        df.to_csv(f"data/{symbol}_raw.csv")
                        
                        print(f"  ✓ Got {len(df)} days of data for {symbol}")
                        return df
                    else:
                        print(f"  ✗ No candle data for {symbol}")
                else:
                    print(f"  ✗ Error: {data.get('message', 'Unknown error')}")
            else:
                print(f"  ✗ Error response: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Exception: {str(e)}")
        
        return None
        
    def check_alerts(self, symbol, df):
        """Check for trading alerts based on technical indicators"""
        if df is None or df.empty or len(df) < 20:  # Need minimum data
            return []
            
        try:
            # Add technical indicators
            df = self.api.add_indicators(df)
                
            # Save with indicators
            df.to_csv(f"data/{symbol}_with_indicators.csv")
                
            # Check for alerts
            alerts = []
            latest = df.iloc[-1]
            
            # RSI alerts
            if 'rsi' in latest and not pd.isna(latest['rsi']):
                if latest['rsi'] > self.alert_conditions["rsi_overbought"]:
                    alerts.append(f"{symbol}: RSI Overbought ({latest['rsi']:.2f})")
                
                if latest['rsi'] < self.alert_conditions["rsi_oversold"]:
                    alerts.append(f"{symbol}: RSI Oversold ({latest['rsi']:.2f})")
            
            # MACD crossover/crossunder
            if len(df) >= 3 and 'macd' in latest and 'macd_signal' in latest:  # Need at least 2 days for comparison
                if not pd.isna(latest['macd']) and not pd.isna(latest['macd_signal']):
                    if self.alert_conditions["macd_crossover"]:
                        if df['macd'].iloc[-2] < df['macd_signal'].iloc[-2] and latest['macd'] > latest['macd_signal']:
                            alerts.append(f"{symbol}: MACD Bullish Crossover")
                        
                    if self.alert_conditions["macd_crossunder"]:
                        if df['macd'].iloc[-2] > df['macd_signal'].iloc[-2] and latest['macd'] < latest['macd_signal']:
                            alerts.append(f"{symbol}: MACD Bearish Crossunder")
            
            # Moving Average alerts
            if self.alert_conditions.get("price_above_sma"):
                sma_key = f"sma_{self.alert_conditions['price_above_sma']}"
                if sma_key in df.columns and not pd.isna(latest[sma_key]) and latest['close'] > latest[sma_key]:
                    alerts.append(f"{symbol}: Price Above {sma_key.upper()}")
                    
            if self.alert_conditions.get("price_below_sma"):
                sma_key = f"sma_{self.alert_conditions['price_below_sma']}"
                if sma_key in df.columns and not pd.isna(latest[sma_key]) and latest['close'] < latest[sma_key]:
                    alerts.append(f"{symbol}: Price Below {sma_key.upper()}")
                    
            # Bollinger Band alerts
            if 'bollinger_high' in latest and 'bollinger_low' in latest:
                if not pd.isna(latest['bollinger_high']) and self.alert_conditions.get("bollinger_breakout_up") and latest['close'] > latest['bollinger_high']:
                    alerts.append(f"{symbol}: Bollinger Band Upper Breakout")
                    
                if not pd.isna(latest['bollinger_low']) and self.alert_conditions.get("bollinger_breakout_down") and latest['close'] < latest['bollinger_low']:
                    alerts.append(f"{symbol}: Bollinger Band Lower Breakout")
                    
            return alerts
        except Exception as e:
            print(f"  ✗ Error checking alerts for {symbol}: {str(e)}")
            return []
                
    def run(self):
        """Run the trading alert system"""
        print("=== TRADING ALERT SYSTEM ===")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Fetch quotes for all symbols
        quotes = self.fetch_quotes()
        
        # 2. Fetch historical data and check for alerts
        print("\n=== ANALYZING TECHNICAL INDICATORS ===")
        
        all_alerts = []
        indicator_summary = {}
        
        for symbol_info in self.symbols:
            symbol = symbol_info["symbol"]
            
            # Get historical data
            df = self.fetch_historical_data(symbol_info)
            
            if df is not None and not df.empty:
                # Check for alerts
                symbol_alerts = self.check_alerts(symbol, df)
                all_alerts.extend(symbol_alerts)
                
                # Store latest indicator values
                if len(df) > 0:
                    try:
                        # Add indicators if needed
                        if 'rsi' not in df.columns:
                            df = self.api.add_indicators(df)
                            
                        latest = df.iloc[-1]
                        indicator_summary[symbol] = {
                            "close": latest['close']
                        }
                        
                        # Only store non-None/non-NaN values
                        for indicator in ['rsi', 'macd', 'macd_signal', 'sma_20', 'sma_50', 'bollinger_high', 'bollinger_low']:
                            if indicator in latest and not pd.isna(latest[indicator]):
                                indicator_summary[symbol][indicator] = latest[indicator]
                    except Exception as e:
                        print(f"  ✗ Error processing indicators for {symbol}: {str(e)}")
        
        # 3. Print trading alerts
        if all_alerts:
            print("\n=== TRADING ALERTS DETECTED ===")
            for alert in all_alerts:
                print(f"🚨 ALERT: {alert}")
        else:
            print("\n✓ No trading alerts detected")
            
        # 4. Print indicator summary
        print("\n=== TECHNICAL INDICATOR SUMMARY ===")
        for symbol, indicators in indicator_summary.items():
            print(f"\n{symbol}:")
            print(f"  Close: ₹{indicators['close']:.2f}")
            
            # Safely print indicators
            if 'rsi' in indicators:
                print(f"  RSI: {indicators['rsi']:.2f}")
            else:
                print(f"  RSI: N/A")
            
            if 'macd' in indicators:
                print(f"  MACD: {indicators['macd']:.2f}")
            else:
                print(f"  MACD: N/A")
            
            if 'macd_signal' in indicators:
                print(f"  MACD Signal: {indicators['macd_signal']:.2f}")
            else:
                print(f"  MACD Signal: N/A")
            
            if 'sma_20' in indicators:
                print(f"  SMA 20: {indicators['sma_20']:.2f}")
            else:
                print(f"  SMA 20: N/A")
            
            if 'sma_50' in indicators:
                print(f"  SMA 50: {indicators['sma_50']:.2f}")
            else:
                print(f"  SMA 50: N/A")
            
            if 'bollinger_low' in indicators and 'bollinger_high' in indicators:
                print(f"  Bollinger Bands: {indicators['bollinger_low']:.2f} - {indicators['bollinger_high']:.2f}")
            else:
                print(f"  Bollinger Bands: N/A")
            
            # Compare with real-time quote
            if symbol in quotes:
                ltp = quotes[symbol]['ltp']
                change = quotes[symbol]['change_percent']
                print(f"  Current: ₹{ltp} ({change}%)")
                
                # Highlight if current price is significantly different from close
                try:
                    if abs((ltp / indicators['close'] - 1) * 100) > 1.0:
                        print(f"  ⚠️ Price has moved {((ltp / indicators['close'] - 1) * 100):.2f}% since last close")
                except:
                    pass
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def set_alert_conditions(self, conditions):
        """Set custom alert conditions
        
        Args:
            conditions (dict): Dictionary of alert conditions to set
            
        Example:
            set_alert_conditions({
                "rsi_overbought": 75,  # RSI level considered overbought
                "rsi_oversold": 25     # RSI level considered oversold
            })
        """
        # Update existing alert conditions with new values
        for key, value in conditions.items():
            if key in self.alert_conditions:
                self.alert_conditions[key] = value
                print(f"Set {key} to {value}")
            else:
                print(f"Warning: Unknown alert condition '{key}'")
        
        # Print current alert conditions
        print("\nCurrent Alert Conditions:")
        for key, value in self.alert_conditions.items():
            print(f"  {key}: {value}")
            
    def get_alert_conditions(self):
        """Get current alert conditions"""
        return self.alert_conditions

if __name__ == "__main__":
    alert_system = TradingAlertSystem()
    alert_system.run() 