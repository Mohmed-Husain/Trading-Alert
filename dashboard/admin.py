from django.contrib import admin
from .models import Stock, Alert, Indicator


admin.site.register(Stock)
admin.site.register(Alert)
admin.site.register(Indicator)


# Register your models here.
