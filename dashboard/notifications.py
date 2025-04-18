import smtplib
import requests
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import json

# Load environment variables
load_dotenv()

class NotificationManager:
    """Class to manage different types of notifications"""
    
    def __init__(self):
        # Email configuration
        self.email_enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
        self.email_from = os.getenv('EMAIL_FROM', '')
        self.email_to = os.getenv('EMAIL_TO', '').split(',')
        self.email_smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.email_smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
        self.email_username = os.getenv('EMAIL_USERNAME', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        
        # SMS configuration (Twilio)
        self.sms_enabled = os.getenv('SMS_ENABLED', 'false').lower() == 'true'
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.twilio_from_number = os.getenv('TWILIO_FROM_NUMBER', '')
        self.twilio_to_numbers = os.getenv('TWILIO_TO_NUMBERS', '').split(',')
    
    def send_email_notification(self, subject, message, email_to=None):
        """Send email notification"""
        if not self.email_enabled:
            print("Email notifications not enabled. Set EMAIL_ENABLED=true in .env file.")
            return False
        
        if not self.email_from or not self.email_username or not self.email_password:
            print("Email configuration incomplete. Check your .env file.")
            return False
        
        # If email_to is provided, use it instead of the default
        recipient_list = email_to if email_to else self.email_to
        
        if not recipient_list:
            print("No recipients specified for email notification.")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = ', '.join(recipient_list)
            msg['Subject'] = subject
            
            # Add message body
            msg.attach(MIMEText(message, 'plain'))
            
            # Connect to server and send email
            server = smtplib.SMTP(self.email_smtp_server, self.email_smtp_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✓ Email notification sent to {', '.join(recipient_list)}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to send email: {str(e)}")
            return False
    
    def send_sms_notification(self, message, phone_numbers=None):
        """Send SMS notification using Twilio"""
        if not self.sms_enabled:
            print("SMS notifications not enabled. Set SMS_ENABLED=true in .env file.")
            return False
            
        if not self.twilio_account_sid or not self.twilio_auth_token or not self.twilio_from_number:
            print("Twilio configuration incomplete. Check your .env file.")
            return False
            
        # If phone_numbers is provided, use it instead of the default
        recipient_numbers = phone_numbers if phone_numbers else self.twilio_to_numbers
        
        if not recipient_numbers:
            print("No recipients specified for SMS notification.")
            return False
            
        try:
            # Truncate message if too long (Twilio has character limits)
            if len(message) > 1600:
                message = message[:1597] + "..."
                
            success_count = 0
            
            # Send to each recipient
            for to_number in recipient_numbers:
                if not to_number.strip():
                    continue
                    
                # API endpoint for Twilio
                url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
                
                # Prepare data for the request
                payload = {
                    'To': to_number.strip(),
                    'From': self.twilio_from_number,
                    'Body': message
                }
                
                # Make the request
                response = requests.post(
                    url,
                    auth=(self.twilio_account_sid, self.twilio_auth_token),
                    data=payload
                )
                
                if response.status_code == 201:
                    success_count += 1
                else:
                    print(f"✗ Failed to send SMS to {to_number}: {response.json().get('message')}")
            
            if success_count > 0:
                print(f"✓ SMS notification sent to {success_count} recipients")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"✗ Failed to send SMS: {str(e)}")
            return False
    
    def notify_user(self, user, subject, message):
        """Send notifications to a user based on their preferences
        
        Args:
            user (User): The user to notify
            subject (str): Subject of the notification
            message (str): Content of the notification
        
        Returns:
            dict: Status of each notification type
        """
        results = {}
        
        try:
            # Get user's notification preferences
            from dashboard.models import UserNotificationPreferences
            
            # Try to get user's preferences, create default if doesn't exist
            preferences, created = UserNotificationPreferences.objects.get_or_create(
                user=user,
                defaults={
                    'email_enabled': True,
                    'sms_enabled': False,
                    'notification_frequency': 'immediate'
                }
            )
            
            # Check notification frequency
            if preferences.notification_frequency == 'daily':
                # For daily notifications, we'd need to implement a queueing system
                # This would be handled elsewhere, so we'll just log it here
                print(f"Queueing notification for daily digest for user {user.username}")
                return {'queued': True}
            
            notification_types = []
            
            # Check if email is enabled for this user
            if preferences.email_enabled:
                notification_types.append('email')
                # Get the user's email directly from user model
                results['email'] = self.send_email_notification(subject, message, [user.email])
            
            # Check if SMS is enabled for this user
            if preferences.sms_enabled and preferences.phone_number:
                notification_types.append('sms')
                # Use the user's phone number
                results['sms'] = self.send_sms_notification(message, [preferences.phone_number])
            
            return results
            
        except Exception as e:
            print(f"✗ Failed to process user notification preferences: {str(e)}")
            return {'error': str(e)}

    def check_alert_conditions(self, alert):
        """Check if the alert conditions are met using AngelOne API data
        
        Args:
            alert (Alert): The alert to check
            
        Returns:
            bool: True if alert condition is met, False otherwise
        """
        from .angel_one import AngelOneAPI
        from .models import Stock, StockGroup
        import json
        
        api = AngelOneAPI()
        if not api.connect():
            print("✗ Failed to connect to Angel One API")
            return False
            
        # Determine stocks to check based on alert type
        stocks_to_check = []
        if alert.alert_type == 'single':
            stocks_to_check = [alert.stock]
        else:  # multiple stocks
            stocks_to_check = alert.stock_group.stocks.all()
            
        triggered_alerts = []
        
        for stock in stocks_to_check:
            # Get historical data for the stock
            from_date = datetime.now() - timedelta(days=30)  # Get data for last 30 days
            to_date = datetime.now()
            
            # Format dates as required by API
            from_date_str = from_date.strftime('%Y-%m-%d')
            to_date_str = to_date.strftime('%Y-%m-%d')
            
            # Get data for the specified timeframe
            dataframe = api.get_historical_data(
                symbol=stock.symbol,
                exchange="NSE",  # Assuming NSE, adjust as needed
                interval=alert.timeframe,
                from_date=from_date_str,
                to_date=to_date_str
            )
            
            if dataframe is None or dataframe.empty:
                print(f"✗ No data available for {stock.symbol}")
                continue
                
            # Parse indicator parameters
            try:
                indicator1_params = json.loads(alert.indicator1_params)
                indicator2_params = json.loads(alert.indicator2_params)
            except json.JSONDecodeError:
                print(f"✗ Invalid JSON in indicator parameters for alert {alert.id}")
                continue
                
            # Get indicator values
            indicator1_value = self._get_indicator_value(dataframe, alert.indicator1.name, indicator1_params)
            indicator2_value = self._get_indicator_value(dataframe, alert.indicator2.name, indicator2_params)
            
            if indicator1_value is None or indicator2_value is None:
                print(f"✗ Could not compute indicator values for alert {alert.id}")
                continue
                
            # Check if condition is met
            is_triggered = False
            if alert.condition == 'above' and indicator1_value > indicator2_value:
                is_triggered = True
            elif alert.condition == 'below' and indicator1_value < indicator2_value:
                is_triggered = True
            elif alert.condition == 'equals' and abs(indicator1_value - indicator2_value) < 0.0001:  # Close enough to equal
                is_triggered = True
                
            if is_triggered:
                triggered_alerts.append({
                    'stock': stock,
                    'indicator1': f"{alert.indicator1.name}({indicator1_params.get('period', '')})",
                    'indicator2': f"{alert.indicator2.name}({indicator2_params.get('period', '')})",
                    'indicator1_value': round(indicator1_value, 2),
                    'indicator2_value': round(indicator2_value, 2),
                    'condition': alert.condition
                })
                
        # If any alerts were triggered, send notification
        if triggered_alerts:
            # Construct message
            subject = f"Trading Alert: {len(triggered_alerts)} condition(s) met"
            message = "The following alert conditions have been met:\n\n"
            
            for triggered in triggered_alerts:
                condition_text = {
                    'above': 'crossed above',
                    'below': 'crossed below',
                    'equals': 'equals'
                }.get(triggered['condition'], triggered['condition'])
                
                message += (f"Stock: {triggered['stock'].symbol} - {triggered['stock'].name}\n"
                           f"{triggered['indicator1']} ({triggered['indicator1_value']}) {condition_text} "
                           f"{triggered['indicator2']} ({triggered['indicator2_value']})\n\n")
                           
            # Send notification to user
            self.notify_user(alert.user, subject, message)
            return True
            
        return False
        
    def _get_indicator_value(self, dataframe, indicator_name, params):
        """Get the latest value of the specified indicator from the dataframe
        
        Args:
            dataframe (DataFrame): Historical price data with indicators
            indicator_name (str): Name of the indicator
            params (dict): Parameters for the indicator
            
        Returns:
            float: The indicator value, or None if it couldn't be computed
        """
        # Get the most recent row
        if dataframe.empty:
            return None
            
        latest = dataframe.iloc[-1]
        period = params.get('period', 14)  # Default period
        
        # Map indicator names to their column names in the dataframe
        indicator_map = {
            'RSI': f'rsi',
            'MACD': f'macd',
            'EMA': f'sma_{period}',  # Using SMA as proxy for EMA
            'SMA': f'sma_{period}',
            'Bollinger Upper': f'bollinger_high',
            'Bollinger Lower': f'bollinger_low',
            'Bollinger Middle': f'bollinger_mid',
            'Price': 'close'
        }
        
        # Get the column name for this indicator
        column = indicator_map.get(indicator_name)
        if not column:
            print(f"✗ Unknown indicator: {indicator_name}")
            return None
            
        # Return the indicator value
        if column in latest:
            return latest[column]
        else:
            print(f"✗ Column {column} not found in dataframe")
            return None
            
    def send_notification(self, subject, message, notification_types=None):
        """Send notifications through all enabled channels or specified channels
        
        Args:
            subject (str): Subject of the notification
            message (str): Content of the notification
            notification_types (list, optional): List of notification types to send.
                                               Defaults to None (all enabled).
        
        Returns:
            dict: Status of each notification type
        """
        results = {}
        
        # Determine which notification types to send
        if notification_types is None:
            # Send all enabled notification types
            notification_types = []
            if self.email_enabled:
                notification_types.append('email')
            if self.sms_enabled:
                notification_types.append('sms')
        
        # Send email if enabled and requested
        if 'email' in notification_types:
            results['email'] = self.send_email_notification(subject, message)
            
        # Send SMS if enabled and requested
        if 'sms' in notification_types:
            results['sms'] = self.send_sms_notification(message)
            
        return results

# Usage example
if __name__ == "__main__":
    # Test notifications
    notifier = NotificationManager()
    
    # Test email
    notifier.send_email_notification("Test Alert", "This is a test trading alert!")
    
    # Test SMS
    notifier.send_sms_notification("ALERT: RELIANCE RSI Overbought (72.5)")
    
    # Test combined notification
    notifier.send_notification("Multiple Trading Alerts", "Several trading conditions met for INFY", 
                              notification_types=['email', 'sms']) 