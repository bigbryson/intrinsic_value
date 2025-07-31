# /apps/holdings/urls.py
from django.urls import path
from .views import holdings_list

app_name = 'holdings'

urlpatterns = [
    path('', holdings_list, name='holdings_list'),
]
