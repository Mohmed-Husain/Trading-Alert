# Trading Alert System

This is a trading alert system that integrates with Angel One API to fetch market data, calculate technical indicators, and generate trading alerts based on predefined conditions.

## Features

- Integration with Angel One API for market data
- Real-time quote data fetching
- Historical price data analysis
- Technical indicators calculation using the TA library
- Customizable alert conditions
- Support for multiple stocks/symbols

## Technical Indicators Supported

- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Simple Moving Averages (SMA) - 20, 50, 200 periods
- ATR (Average True Range)

## Alert Conditions

The system supports various alert conditions, including:

- RSI overbought/oversold levels
- MACD crossovers and crossunders
- Price crossing above/below moving averages
- Bollinger Band breakouts

## Setup

1. Clone the repository
2. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Angel One credentials:
   ```
   ANGEL_API_KEY=your_api_key
   ANGEL_CLIENT_ID=your_client_id
   ANGEL_PASSWORD=your_password
   ANGEL_TOKEN=your_token
   CLIENT_LOCAL_IP=your_local_ip
   CLIENT_PUBLIC_IP=your_public_ip
   MAC_ADDRESS=your_mac_address
   ```

## Usage

Run the trading alerts script:

```bash
python dashboard/trading_alerts.py
```

## Customizing Alert Conditions

Edit the `alert_conditions` dictionary in `dashboard/trading_alerts.py` to customize alert triggers:

```python
alert_conditions = {
    "rsi_overbought": 70,  # RSI level considered overbought
    "rsi_oversold": 30,    # RSI level considered oversold
    "macd_crossover": True,  # Alert on MACD crossing above signal line
    "macd_crossunder": True, # Alert on MACD crossing below signal line
    "price_above_sma": 50,   # Alert when price crosses above SMA50
    "price_below_sma": 20,   # Alert when price crosses below SMA20
    "bollinger_breakout_up": True,   # Alert on upper Bollinger Band breakout
    "bollinger_breakout_down": True  # Alert on lower Bollinger Band breakout
}
```

## Adding New Symbols

Edit the `symbols_to_watch` list in `dashboard/trading_alerts.py` to add or remove symbols:

```python
symbols_to_watch = [
    {"symbol": "RELIANCE", "token": "2885", "exchange": "NSE"},
    {"symbol": "INFY", "token": "1594", "exchange": "NSE"},
    {"symbol": "HDFCBANK", "token": "1333", "exchange": "NSE"}
]
```

## Important Notes

- The system doesn't store data in CSV files, it performs real-time analysis and provides output
- Angel One API authentication token may need to be refreshed periodically
- The system is for informational purposes only and should not be considered investment advice 