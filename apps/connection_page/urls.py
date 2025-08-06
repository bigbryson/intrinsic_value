# /apps/connection_page/urls.py
from django.urls import path
from . import views

app_name = 'connection_page'

urlpatterns = [
    # Schwab URLs
    path('schwab/authenticate/', views.schwab_authenticate, name='schwab_authenticate'),
    path('schwab/callback/', views.schwab_callback, name='schwab_callback'),

    # E*TRADE URLs
    path('etrade/authenticate/', views.etrade_authenticate, name='etrade_authenticate'),
    path('etrade/callback/', views.etrade_callback, name='etrade_callback'),
]
