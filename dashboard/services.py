from django.core.mail import send_mail
from .models import Alert, Stock
from .utils import get_historical_data, calculate_indicator, check_crossover
from .notifications import NotificationManager
import json

def check_alerts():
    alerts = Alert.objects.filter(is_active=True)
    for alert in alerts:
        # Handle single stock alerts
        if alert.alert_type == 'single':
            check_single_stock_alert(alert)
        # Handle multiple stock alerts
        else:
            check_multiple_stocks_alert(alert)

def check_single_stock_alert(alert):
    """Check an alert for a single stock"""
    if not alert.stock:
        return
        
    # Get historical data for the stock
    historical_data = get_historical_data(alert.stock.symbol, alert.timeframe)
    
    if historical_data is not None:
        # Check if conditions are met and trigger alert if they are
        is_triggered, indicator1_value, indicator2_value = check_alert_conditions(
            historical_data, alert
        )
        
        if is_triggered:
            # Send notification using the notification manager
            send_alert_notification(
                alert.user, 
                alert, 
                alert.stock.symbol,
                indicator1_value, 
                indicator2_value
            )
            
            # Disable alert after it's triggered
            alert.is_active = False
            alert.save()

def check_multiple_stocks_alert(alert):
    """Check an alert for multiple stocks in a group"""
    if not alert.stock_group:
        return
        
    triggered_stocks = []
    trigger_details = []
    
    # Check each stock in the group
    for stock in alert.stock_group.stocks.all():
        historical_data = get_historical_data(stock.symbol, alert.timeframe)
        
        if historical_data is not None:
            # Check if conditions are met for this stock
            is_triggered, indicator1_value, indicator2_value = check_alert_conditions(
                historical_data, alert
            )
            
            if is_triggered:
                triggered_stocks.append(stock)
                trigger_details.append({
                    'symbol': stock.symbol,
                    'indicator1_value': indicator1_value,
                    'indicator2_value': indicator2_value
                })
    
    # If any stock triggered the alert, send notification
    if triggered_stocks:
        send_multiple_stocks_alert_notification(
            alert.user,
            alert,
            trigger_details
        )
        
        # Disable alert after it's triggered
        alert.is_active = False
        alert.save()

def check_alert_conditions(historical_data, alert):
    """Check if alert conditions are met for the given historical data"""
    # Calculate indicator 1 value
    indicator1_value = calculate_indicator(
        historical_data, 
        alert.indicator1.name, 
        alert.indicator1_params
    )
    
    # Calculate indicator 2 value
    indicator2_value = calculate_indicator(
        historical_data, 
        alert.indicator2.name, 
        alert.indicator2_params
    )
    
    # Check if the condition is met
    is_triggered = check_crossover(indicator1_value, indicator2_value, alert.condition)
    
    return is_triggered, indicator1_value, indicator2_value

def send_alert_notification(user, alert, symbol, indicator1_value, indicator2_value):
    """Send notification to user based on their preferences"""
    subject = f"Trading Alert Triggered for {symbol}"
    
    # Get indicator names and parameters in a readable format
    indicator1_str, indicator2_str, condition_str = format_alert_condition(alert)
    
    message = f"Hello {user.username},\n\n" \
              f"Your alert for {symbol} has been triggered.\n\n" \
              f"Condition: {indicator1_str} {condition_str} {indicator2_str}\n" \
              f"Current {indicator1_str} value: {indicator1_value:.4f}\n" \
              f"Current {indicator2_str} value: {indicator2_value:.4f}\n\n" \
              f"Timeframe: {alert.timeframe}\n\n" \
              f"Check your dashboard for more details."
    
    # Use NotificationManager to send notification based on user preferences
    notifier = NotificationManager()
    return notifier.notify_user(user, subject, message)

def send_multiple_stocks_alert_notification(user, alert, trigger_details):
    """Send notification for multiple stocks alert based on user preferences"""
    subject = f"Trading Alert Triggered for Multiple Stocks"
    
    # Get indicator names and parameters in a readable format
    indicator1_str, indicator2_str, condition_str = format_alert_condition(alert)
    
    message = f"Hello {user.username},\n\n" \
              f"Your group alert for {alert.stock_group.name} has been triggered by the following stocks:\n\n"
              
    for detail in trigger_details:
        message += f"Stock: {detail['symbol']}\n" \
                  f"Condition: {indicator1_str} {condition_str} {indicator2_str}\n" \
                  f"Current {indicator1_str} value: {detail['indicator1_value']:.4f}\n" \
                  f"Current {indicator2_str} value: {detail['indicator2_value']:.4f}\n\n"
    
    message += f"Timeframe: {alert.timeframe}\n\n" \
               f"Check your dashboard for more details."
    
    # Use NotificationManager to send notification based on user preferences
    notifier = NotificationManager()
    return notifier.notify_user(user, subject, message)

def format_alert_condition(alert):
    """Format the alert condition components for display"""
    try:
        # Extract period values from parameters
        params1 = json.loads(alert.indicator1_params)
        params2 = json.loads(alert.indicator2_params)
        
        # Format indicator names with periods
        period1 = params1.get('period', '')
        period2 = params2.get('period', '')
        
        indicator1_str = f"{alert.indicator1.name}({period1})" if period1 else alert.indicator1.name
        indicator2_str = f"{alert.indicator2.name}({period2})" if period2 else alert.indicator2.name
    except:
        indicator1_str = alert.indicator1.name
        indicator2_str = alert.indicator2.name
    
    # Format condition for readability
    if alert.condition == "above":
        condition_str = "crossed above"
    elif alert.condition == "below":
        condition_str = "crossed below"
    else:
        condition_str = "equals"
        
    return indicator1_str, indicator2_str, condition_str
