from django.urls import path 
from . import views
from django.http import request




urlpatterns=[
    path('', views.home, name='dashboard-home'),
    ]