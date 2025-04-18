from django.contrib import admin
from .models import Stock, StockGroup, Indicator, Alert, UserNotificationPreferences


admin.site.register(Stock)
admin.site.register(StockGroup)
admin.site.register(Indicator)
admin.site.register(Alert)
admin.site.register(UserNotificationPreferences)


# Register your models here.
