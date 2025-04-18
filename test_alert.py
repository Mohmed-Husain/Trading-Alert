import os
import sys
import django
from datetime import datetime
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TradingAlert.settings')
django.setup()

# Import Django models
from django.contrib.auth.models import User
from dashboard.models import Alert
from dashboard.notifications import NotificationManager

def test_single_alert():
    """Test checking a specific alert"""
    alert_id = input("Enter the ID of the alert to check: ")
    
    try:
        alert = Alert.objects.get(id=alert_id)
        print(f"\nFound alert #{alert.id}:")
        print(f"  User: {alert.user.username}")
        if alert.alert_type == 'single':
            print(f"  Stock: {alert.stock.symbol} ({alert.stock.name})")
        else:
            print(f"  Stock Group: {alert.stock_group.name}")
        
        indicator1_params = json.loads(alert.indicator1_params)
        indicator2_params = json.loads(alert.indicator2_params)
        
        print(f"  Condition: {alert.indicator1.name}({indicator1_params.get('period', '')}) {alert.condition} {alert.indicator2.name}({indicator2_params.get('period', '')})")
        print(f"  Timeframe: {alert.timeframe}")
        
        # Check if the alert condition is met
        print("\nChecking if alert condition is met...")
        notification_manager = NotificationManager()
        
        # This will check the alert and send a notification if triggered
        if notification_manager.check_alert_conditions(alert):
            print("\n✓ Alert condition was triggered! Notification sent.")
        else:
            print("\n✗ Alert condition was not triggered at this time.")
            
        return True
        
    except Alert.DoesNotExist:
        print(f"Alert with ID '{alert_id}' not found.")
        return False
    except Exception as e:
        print(f"Error checking alert: {str(e)}")
        return False

def list_all_alerts():
    """List all active alerts in the system"""
    alerts = Alert.objects.filter(is_active=True).order_by('user__username')
    
    if not alerts:
        print("No active alerts found in the system.")
        return
        
    print(f"\nFound {alerts.count()} active alerts:")
    print("-" * 80)
    print(f"{'ID':<5} {'User':<15} {'Type':<10} {'Stock/Group':<15} {'Condition':<30}")
    print("-" * 80)
    
    for alert in alerts:
        try:
            indicator1_params = json.loads(alert.indicator1_params)
            indicator2_params = json.loads(alert.indicator2_params)
            
            if alert.alert_type == 'single':
                target = alert.stock.symbol if alert.stock else "N/A"
            else:
                target = f"{alert.stock_group.name} (Group)" if alert.stock_group else "N/A"
                
            condition = f"{alert.indicator1.name}({indicator1_params.get('period', '')}) {alert.condition} {alert.indicator2.name}({indicator2_params.get('period', '')})"
            
            print(f"{alert.id:<5} {alert.user.username:<15} {alert.alert_type:<10} {target:<15} {condition:<30}")
        except:
            print(f"{alert.id:<5} {alert.user.username:<15} {alert.alert_type:<10} ERROR PARSING ALERT")
            
    print("-" * 80)

def send_fake_alert():
    """Send a fake alert via email"""
    notification_manager = NotificationManager()
    
    # Prepare email content
    subject = "🔔 Trading Alert: RELIANCE"
    message = """
    ⚠️ ALERT TRIGGERED ⚠️
    
    Symbol: RELIANCE
    Alert Type: RSI
    Condition: RSI > 70 (Overbought)
    Value: 72.5
    
    This is a test alert to verify the notification system.
    """
    
    # Send email
    email_sent = notification_manager.send_email_notification(
        subject=subject,
        message=message,
        email_to=[os.getenv('TEST_EMAIL')]
    )
    
    if email_sent:
        print("✅ Test alert email sent successfully!")
    else:
        print("❌ Failed to send test alert email")

if __name__ == "__main__":
    print("=== Trading Alert System Test ===")
    print("1. Check specific alert")
    print("2. List all active alerts")
    print("3. Send a fake alert")
    
    choice = input("\nEnter your choice (1/2/3): ")
    
    if choice == "1":
        test_single_alert()
    elif choice == "2":
        list_all_alerts()
    elif choice == "3":
        send_fake_alert()
    else:
        print("Invalid choice. Please enter 1, 2, or 3.") 