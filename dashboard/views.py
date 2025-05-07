from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from .models import Alert, StockGroup, UserNotificationPreferences, AlertLog
from .forms import AlertForm, StockGroupForm, UserNotificationPreferencesForm

@login_required
def home(request):
    alerts = Alert.objects.filter(user=request.user)
    stock_groups = StockGroup.objects.filter(user=request.user)

    if request.method == 'POST':
        form = AlertForm(request.POST, user=request.user)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = request.user  # Assign logged-in user
            alert.save()
            messages.success(request, 'Alert created successfully!')
            return redirect('dashboard-home')  # Redirect to refresh alerts list

    else:
        form = AlertForm(user=request.user)

    return render(request, 'dashboard/home.html', {
        'alerts': alerts, 
        'stock_groups': stock_groups,
        'form': form
    })

@login_required
def delete_alert(request, alert_id):
    alert = get_object_or_404(Alert, id=alert_id)
    
    # Security check: ensure the user owns this alert
    if alert.user != request.user:
        return HttpResponseForbidden("You don't have permission to delete this alert.")
    
    # Delete the alert
    alert.delete()
    messages.success(request, 'Alert deleted successfully!')
    
    # Redirect back to the dashboard
    return redirect('dashboard-home')

@login_required
def notification_preferences(request):
    """View for users to manage their notification preferences"""
    # Try to get existing preferences or create new ones
    try:
        preferences = UserNotificationPreferences.objects.get(user=request.user)
    except UserNotificationPreferences.DoesNotExist:
        # Create default preferences
        preferences = UserNotificationPreferences(
            user=request.user,
            email_enabled=True,
            sms_enabled=False,
            notification_frequency='immediate'
        )
        preferences.save()
        
    if request.method == 'POST':
        form = UserNotificationPreferencesForm(request.POST, instance=preferences)
        if form.is_valid():
            # Apply the form data to the instance
            preferences = form.save(commit=False)
            # Ensure the user field is set
            preferences.user = request.user
            # Save to database
            preferences.save()
            messages.success(request, 'Notification preferences updated successfully!')
            return redirect('dashboard-home')  # Redirect to home page after saving
        else:
            # If form is invalid, show errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = UserNotificationPreferencesForm(instance=preferences)
        
    return render(request, 'dashboard/notification_preferences.html', {
        'form': form,
        'title': 'Notification Preferences'
    })

@login_required
def stock_group_list(request):
    stock_groups = StockGroup.objects.filter(user=request.user)
    return render(request, 'dashboard/stock_group_list.html', {'stock_groups': stock_groups})

@login_required
def stock_group_create(request):
    if request.method == 'POST':
        form = StockGroupForm(request.POST, user=request.user)
        if form.is_valid():
            group = form.save()
            messages.success(request, f'Stock group "{group.name}" created successfully!')
            return redirect('stock-group-list')
    else:
        form = StockGroupForm(user=request.user)
    
    return render(request, 'dashboard/stock_group_form.html', {'form': form, 'title': 'Create Stock Group'})

@login_required
def stock_group_update(request, group_id):
    group = get_object_or_404(StockGroup, id=group_id)
    
    # Security check: ensure the user owns this group
    if group.user != request.user:
        return HttpResponseForbidden("You don't have permission to edit this stock group.")
    
    if request.method == 'POST':
        form = StockGroupForm(request.POST, instance=group, user=request.user)
        if form.is_valid():
            group = form.save()
            messages.success(request, f'Stock group "{group.name}" updated successfully!')
            return redirect('stock-group-list')
    else:
        form = StockGroupForm(instance=group, user=request.user)
    
    return render(request, 'dashboard/stock_group_form.html', {'form': form, 'title': 'Update Stock Group'})

@login_required
def stock_group_delete(request, group_id):
    group = get_object_or_404(StockGroup, id=group_id)
    
    # Security check: ensure the user owns this group
    if group.user != request.user:
        return HttpResponseForbidden("You don't have permission to delete this stock group.")
    
    if request.method == 'POST':
        group_name = group.name
        group.delete()
        messages.success(request, f'Stock group "{group_name}" deleted successfully!')
        return redirect('stock-group-list')
    
    return render(request, 'dashboard/stock_group_confirm_delete.html', {'group': group})

@login_required
def alerts_view(request):
    # Get all alerts for the user
    all_alerts = Alert.objects.filter(user=request.user)
    
    # Separate active and triggered alerts
    active_alerts = all_alerts.filter(is_active=True)
    triggered_alerts = all_alerts.filter(is_active=False)
    
    # Get alert logs
    alert_logs = AlertLog.objects.filter(alert__user=request.user)[:50]  # Limit to last 50 logs
    
    context = {
        'active_alerts': active_alerts,
        'triggered_alerts': triggered_alerts,
        'all_alerts': all_alerts,
        'alert_logs': alert_logs,
    }
    
    return render(request, 'dashboard/alerts.html', context)
