from django.core.management.base import BaseCommand
from dashboard.models import Alert
from dashboard.notifications import NotificationManager
import time
import logging
import os
from django.conf import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check alert conditions for all active alerts and send notifications'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=300,  # Default 5 minutes (300 seconds)
            help='Interval in seconds between checks'
        )
        
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run only once instead of continuously'
        )
        
    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['once']
        
        notification_manager = NotificationManager()
        self.stdout.write(self.style.SUCCESS('Started alert checking service'))
        
        try:
            while True:
                try:
                    self.check_alerts(notification_manager)
                except Exception as e:
                    error_msg = str(e).lower()
                    # Check for token expiration
                    if 'token' in error_msg or 'auth' in error_msg or 'expire' in error_msg:
                        self.stdout.write(
                            self.style.ERROR('Authentication error - your Angel One API token may have expired!')
                        )
                        self.stdout.write(
                            self.style.WARNING('Please update the ANGEL_TOKEN value in your .env file with a new token.')
                        )
                        # If token error, exit the loop if running once, otherwise wait and retry
                        if run_once:
                            break
                    else:
                        # For other errors, log and continue
                        logger.error(f"Error during alert check: {str(e)}", exc_info=True)
                        self.stdout.write(self.style.ERROR(f'Error during alert check: {str(e)}'))
                
                if run_once:
                    break
                    
                # Wait for the next check
                self.stdout.write(f'Waiting {interval} seconds until next check...')
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Alert checking service stopped by user'))
            
    def check_alerts(self, notification_manager):
        """Check all active alerts for conditions"""
        self.stdout.write('Checking alerts...')
        
        # Get all active alerts
        alerts = Alert.objects.filter(is_active=True)
        
        if not alerts:
            self.stdout.write('No active alerts found')
            return
            
        self.stdout.write(f'Found {alerts.count()} active alerts')
        
        # Check each alert
        for alert in alerts:
            try:
                self.stdout.write(f'Checking alert #{alert.id} for user {alert.user.username}')
                
                # Check if alert condition is met and send notification if needed
                if notification_manager.check_alert_conditions(alert):
                    self.stdout.write(
                        self.style.SUCCESS(f'Alert #{alert.id} triggered - notification sent to {alert.user.username}')
                    )
                else:
                    self.stdout.write(f'Alert #{alert.id} conditions not met')
                    
            except Exception as e:
                logger.error(f"Error checking alert #{alert.id}: {str(e)}", exc_info=True)
                self.stdout.write(
                    self.style.ERROR(f'Error checking alert #{alert.id}: {str(e)}')
                )
                
        self.stdout.write(self.style.SUCCESS('Finished checking alerts')) 