# /apps/grahams_table/urls.py
from django.urls import path
from .views import grahams_table_view, stock_detail_view

app_name = 'grahams_table'

urlpatterns = [
    # URL for the main list of stocks
    path('', grahams_table_view, name='grahams_table_list'),

    # URL for the detail page of a single stock
    # Example: /grahams-table/stock/AAPL/
    path('stock/<str:symbol>/', stock_detail_view, name='stock_detail'),
]
