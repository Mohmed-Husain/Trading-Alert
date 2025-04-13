from django import forms
from .models import Alert, StockGroup, Stock, Indicator
import json

class StockGroupForm(forms.ModelForm):
    stocks = forms.ModelMultipleChoiceField(
        queryset=Stock.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        help_text="Select multiple stocks to include in this group"
    )
    
    class Meta:
        model = StockGroup
        fields = ['name', 'stocks']
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(StockGroupForm, self).__init__(*args, **kwargs)
        if user:
            self.instance.user = user

class AlertForm(forms.ModelForm):
    # Add help text for parameter fields
    alert_type = forms.ChoiceField(
        choices=Alert.ALERT_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial='single',
        help_text="Choose whether to set up an alert for a single stock or multiple stocks"
    )
    
    # Simplified parameter inputs
    period1 = forms.IntegerField(
        min_value=1, 
        max_value=500,
        initial=90,
        help_text="Period for the first indicator (e.g., 90 for EMA(90))"
    )
    
    period2 = forms.IntegerField(
        min_value=1, 
        max_value=500,
        initial=200,
        help_text="Period for the second indicator (e.g., 200 for EMA(200))"
    )
    
    # Hidden fields to store the actual JSON
    indicator1_params = forms.CharField(required=False, widget=forms.HiddenInput())
    indicator2_params = forms.CharField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = Alert
        fields = ['alert_type', 'stock', 'stock_group', 'indicator1', 'period1', 
                 'condition', 'indicator2', 'period2', 'timeframe', 
                 'indicator1_params', 'indicator2_params']
        widgets = {
            'condition': forms.Select(choices=[("above", "Crosses Above"), ("below", "Crosses Below"), ("equals", "Equals")]),
            'timeframe': forms.Select(choices=[
                ("1min", "1 Minute"), 
                ("5min", "5 Minutes"), 
                ("15min", "15 Minutes"),
                ("4h", "4 Hours"),
                ("1day", "1 Day"),
                ("1week", "1 Week")
            ]),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(AlertForm, self).__init__(*args, **kwargs)
        
        if user:
            self.instance.user = user
            # Filter stock_group choices to only show the user's groups
            self.fields['stock_group'].queryset = StockGroup.objects.filter(user=user)
            
        # If we're editing an existing alert, populate the period fields
        if self.instance and self.instance.pk:
            try:
                # Extract period from indicator1_params
                params1 = json.loads(self.instance.indicator1_params)
                if 'period' in params1:
                    self.initial['period1'] = params1['period']
                
                # Extract period from indicator2_params
                params2 = json.loads(self.instance.indicator2_params)
                if 'period' in params2:
                    self.initial['period2'] = params2['period']
            except:
                pass
    
    def clean(self):
        cleaned_data = super().clean()
        alert_type = cleaned_data.get('alert_type')
        stock = cleaned_data.get('stock')
        stock_group = cleaned_data.get('stock_group')
        
        # Convert simple period inputs to JSON params
        period1 = cleaned_data.get('period1')
        period2 = cleaned_data.get('period2')
        
        # Create JSON for indicator1
        indicator1_params = json.dumps({"period": period1})
        cleaned_data['indicator1_params'] = indicator1_params
        
        # Create JSON for indicator2
        indicator2_params = json.dumps({"period": period2})
        cleaned_data['indicator2_params'] = indicator2_params
        
        if alert_type == 'single' and not stock:
            self.add_error('stock', 'This field is required for single stock alerts.')
        
        if alert_type == 'multiple' and not stock_group:
            self.add_error('stock_group', 'This field is required for multiple stock alerts.')
        
        return cleaned_data
