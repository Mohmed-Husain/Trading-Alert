from smartapi import SmartConnect
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta

load_dotenv()

class AngelOneAPI:
    def __init__(self):
        self.api_key = os.getenv('ANGEL_API_KEY')
        self.client_id = os.getenv('ANGEL_CLIENT_ID')
        self.password = os.getenv('ANGEL_PASSWORD')
        self.token = os.getenv('ANGEL_TOKEN')
        self.smart_api = None
        
    def connect(self):
        """Initialize connection to Angel One API"""
        try:
            self.smart_api = SmartConnect(
                api_key=self.api_key,
                clientId=self.client_id,
                password=self.password,
                access_token=self.token
            )
            return True
        except Exception as e:
            print(f"Error connecting to Angel One API: {str(e)}")
            return False
            
    def get_historical_data(self, symbol, exchange, interval, from_date, to_date):
        """Get historical data for a symbol"""
        try:
            if not self.smart_api:
                if not self.connect():
                    return None
                    
            data = self.smart_api.getCandleData(
                exchange=exchange,
                tradingsymbol=symbol,
                interval=interval,
                fromdate=from_date,
                todate=to_date
            )
            
            # Convert to pandas DataFrame
            df = pd.DataFrame(data)
            if not df.empty:
                df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            return df
            
        except Exception as e:
            print(f"Error fetching historical data: {str(e)}")
            return None
            
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