from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.symbol})"

class StockGroup(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stocks = models.ManyToManyField(Stock)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.stocks.count()} stocks)"

class Indicator(models.Model):
    name = models.CharField(max_length=50, unique=True)
    # description = models.TextField()

    def __str__(self):
        return self.name

class UserNotificationPreferences(models.Model):
    """User notification preferences"""
    FREQUENCY_CHOICES = [
        ('immediate', 'Immediate'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    email_enabled = models.BooleanField(default=True, help_text="Enable email notifications")
    sms_enabled = models.BooleanField(default=False, help_text="Enable SMS notifications")
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Phone number for SMS notifications")
    notification_frequency = models.CharField(
        max_length=20, 
        choices=FREQUENCY_CHOICES,
        default='immediate',
        help_text="How frequently notifications should be sent"
    )
    
    def __str__(self):
        return f"{self.user.username}'s notification preferences"
        
    def clean(self):
        """Validate the model"""
        if self.sms_enabled and not self.phone_number:
            raise ValidationError({
                'phone_number': 'Phone number is required when SMS notifications are enabled'
            })
            
    def save(self, *args, **kwargs):
        """Override save to ensure clean is called"""
        self.clean()
        return super().save(*args, **kwargs)
    
    @property
    def email_address(self):
        """Get the user's email address from their profile"""
        return self.user.email

class Alert(models.Model):
    ALERT_TYPE_CHOICES = [
        ('single', 'Single Stock'),
        ('multiple', 'Multiple Stocks')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link alert to a user
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPE_CHOICES, default='single')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, null=True, blank=True)
    stock_group = models.ForeignKey(StockGroup, on_delete=models.CASCADE, null=True, blank=True)
    indicator1 = models.ForeignKey(Indicator, on_delete=models.CASCADE, related_name="indicator1_alerts")
    indicator1_params = models.CharField(max_length=50, default="{}") # Store parameters like period as JSON string
    condition = models.CharField(max_length=20, choices=[("above", "Crosses Above"), ("below", "Crosses Below"), ("equals", "Equals")])
    indicator2 = models.ForeignKey(Indicator, on_delete=models.CASCADE, related_name="indicator2_alerts")
    indicator2_params = models.CharField(max_length=50, default="{}") # Store parameters like period as JSON string
    timeframe = models.CharField(max_length=10, choices=[
        ("1min", "1 Minute"), 
        ("5min", "5 Minutes"), 
        ("15min", "15 Minutes"), 
        ("4h", "4 Hours"),
        ("1day", "1 Day"),
        ("1week", "1 Week")
    ])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.alert_type == 'single':
            return f"{self.user.username} - {self.stock} Alert"
        else:
            return f"{self.user.username} - Group: {self.stock_group.name} Alert"
            
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validate that either stock or stock_group is set based on alert_type
        if self.alert_type == 'single' and not self.stock:
            raise ValidationError("Single stock alert must have a stock selected")
        elif self.alert_type == 'multiple' and not self.stock_group:
            raise ValidationError("Multiple stocks alert must have a stock group selected")

class AlertLog(models.Model):
    EVENT_TYPES = [
        ('created', 'Created'),
        ('triggered', 'Triggered'),
        ('deleted', 'Deleted'),
        ('modified', 'Modified'),
    ]
    
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='logs')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    stock_symbol = models.CharField(max_length=10)
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.stock_symbol} - {self.event_type} at {self.timestamp}"