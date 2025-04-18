# Trading Alert System

The Trading Alert System is a real-time, event-driven platform designed to assist traders by generating timely alerts based on technical analysis. It seamlessly integrates with the Angel One SmartAPI to fetch live market data (such as candlestick data), processes it to calculate a variety of technical indicators, and triggers alerts when predefined trading conditions are met.

This system is ideal for traders who rely on technical strategies and want to be notified when specific market conditions are fulfilled—without needing to constantly monitor charts.


![](https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExd2hlcWtrcHlyYXMxeGg2ZXMzdWZqcHNwcmo3M2l4aTQzcDQ4MzhldyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/HHgLbMDYHNt0mo1Wdo/giphy.gif)

### 🧱 Tech Stack

| Layer            | Technology/Tool                                     | Description                                                                 |
|------------------|------------------------------------------------------|-----------------------------------------------------------------------------|
| **Backend**       | Django                                               | Core web framework handling business logic, routing, and APIs              |
|                  | Celery + Redis                                       | For scheduling and running background tasks (e.g., checking alerts)        |
|                  | Angel One SmartAPI                                   | Fetches real-time stock/candle data                                        |
| **Data Processing** | Pandas, NumPy                                      | Indicator calculation and data manipulation                                |
| **Frontend**      | HTML, CSS, JavaScript, Bootstrap                     | Simple user dashboard for configuration and alerts                         |
| **Email**         | SMTP (via Django)                                    | Sending real-time alert notifications to users                             |
| **Database**      | SQLite (for local dev)                               | Stores user data, alert configurations, etc.                               |
<!-- | **Deployment**    | AWS EC2 / Render / Railway (based on project needs) | Hosting the Django app                                                     | -->
| **Version Control**| Git & GitHub                                        | Code management and collaboration                                          |
<!-- | **Others**        | dotenv, logging, gunicorn, Nginx (for production)    | Environment and production setup                                           | -->


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