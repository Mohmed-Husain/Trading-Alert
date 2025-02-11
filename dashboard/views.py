from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.http import request


def home(request):
    return render(request, 'dashboard/home.html')
