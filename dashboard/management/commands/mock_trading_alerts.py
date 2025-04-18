import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ta  # Technical analysis library for indicators

class MockAngelOneAPI:
    def __init__(self):
        """Initialize mock API"""
        pass
        
    def generate_mock_data(self, symbol, days=60):
        """Generate mock historical price data for testing with patterns that trigger alerts"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Generate random price data with specific patterns based on symbol
        if symbol == "RELIANCE":
            # Higher price range for RELIANCE with a recent bullish trend
            base_price = 2500
            volatility = 50
            
            # Create price series with some pattern
            closes = np.zeros(len(date_range))
            closes[0] = base_price
            
            # First half with downtrend
            for i in range(1, len(date_range)//2):
                daily_change = np.random.normal(-0.002, volatility/base_price/2)
                closes[i] = closes[i-1] * (1 + daily_change)
            
            # Second half with uptrend (bullish reversal)
            for i in range(len(date_range)//2, len(date_range)):
                daily_change = np.random.normal(0.003, volatility/base_price/2)
                closes[i] = closes[i-1] * (1 + daily_change)
            
            # Create a MACD crossover in the last few days
            closes[-5:] = closes[-5] * np.array([1.0, 1.01, 1.02, 1.03, 1.035])
            
        elif symbol == "INFY":
            # INFY with overbought RSI and approaching upper bollinger band
            base_price = 1500
            volatility = 30
            
            # Create price series with some pattern
            closes = np.zeros(len(date_range))
            closes[0] = base_price
            
            # Slight uptrend, then strong momentum at the end
            for i in range(1, len(date_range)-10):
                daily_change = np.random.normal(0.0005, volatility/base_price/3)
                closes[i] = closes[i-1] * (1 + daily_change)
            
            # Strong bullish momentum in the last 10 days (will trigger overbought RSI)
            for i in range(len(date_range)-10, len(date_range)):
                daily_change = np.random.normal(0.006, volatility/base_price/4)
                closes[i] = closes[i-1] * (1 + daily_change)
                
        else: # HDFCBANK
            # HDFCBANK below SMA50 and approaching lower bollinger band
            base_price = 1000
            volatility = 20
            
            # Create price series with some pattern
            closes = np.zeros(len(date_range))
            closes[0] = base_price
            
            # First 40 days with slight uptrend
            for i in range(1, 40):
                daily_change = np.random.normal(0.001, volatility/base_price/3)
                closes[i] = closes[i-1] * (1 + daily_change)
            
            # Last 20 days with downtrend (will go below SMA50)
            for i in range(40, len(date_range)):
                daily_change = np.random.normal(-0.004, volatility/base_price/3)
                closes[i] = closes[i-1] * (1 + daily_change)
            
            # Extra drop in the last few days
            closes[-5:] = closes[-5] * np.array([1.0, 0.99, 0.98, 0.975, 0.97])
            
        # Calculate other price values based on close
        opens = closes * (1 + np.random.normal(0, 0.005, len(closes)))
        highs = np.maximum(opens, closes) * (1 + np.abs(np.random.normal(0, 0.01, len(closes))))
        lows = np.minimum(opens, closes) * (1 - np.abs(np.random.normal(0, 0.01, len(closes))))
        volumes = np.random.normal(1000000, 200000, len(closes)).astype(int)
        volumes = np.abs(volumes)
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': date_range,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes
        })
        
        df.set_index('timestamp', inplace=True)
        return df
        
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

def main():
    # Initialize Mock API
    api = MockAngelOneAPI()
    
    # Set up symbols to watch
    symbols_to_watch = ["RELIANCE", "INFY", "HDFCBANK"]
    
    # Set up alert conditions (with more sensitive thresholds to trigger alerts)
    alert_conditions = {
        "rsi_overbought": 50,   # Lower the overbought threshold (normal is 70)
        "rsi_oversold": 50,     # Raise the oversold threshold (normal is 30)
        "macd_crossover": True,
        "macd_crossunder": True,
        "price_above_sma": 50,
        "price_below_sma": 20,
        "bollinger_breakout_up": True,
        "bollinger_breakout_down": True
    }
    
    # Process each symbol
    all_alerts = []
    for symbol in symbols_to_watch:
        print(f"Processing {symbol}...")
        
        # Generate mock historical data
        df = api.generate_mock_data(symbol)
        
        if df is not None and not df.empty:
            # Add technical indicators
            df = api.add_indicators(df)
            
            # Check for alerts
            alerts = api.check_alerts(df, symbol, alert_conditions)
            all_alerts.extend(alerts)
            
            # Print latest indicator values
            latest = df.iloc[-1]
            print(f"\n--- {symbol} Latest Indicator Values ---")
            print(f"Date: {df.index[-1].strftime('%Y-%m-%d')}")
            print(f"Close: {latest['close']:.2f}")
            print(f"RSI: {latest['rsi']:.2f}")
            print(f"MACD: {latest['macd']:.2f}")
            print(f"MACD Signal: {latest['macd_signal']:.2f}")
            print(f"SMA 20: {latest['sma_20']:.2f}")
            print(f"SMA 50: {latest['sma_50']:.2f}")
            print(f"Bollinger Upper: {latest['bollinger_high']:.2f}")
            print(f"Bollinger Lower: {latest['bollinger_low']:.2f}")
            print(f"ATR: {latest['atr']:.2f}")
            
        else:
            print(f"Failed to generate mock data for {symbol}")
        
        print("-" * 50)
    
    # Print all alerts
    if all_alerts:
        print("\n=== TRADING ALERTS ===")
        for alert in all_alerts:
            print(f"ALERT: {alert}")
    else:
        print("\nNo alerts triggered.")

if __name__ == "__main__":
    main() 