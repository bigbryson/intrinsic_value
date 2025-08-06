# /apps/grahams_table/urls.py
from django.urls import path
# Import the class-based views from your new views.py file
from .views import StockScreenerPageView, StockDetailView

app_name = 'grahams_table'

urlpatterns = [
    # URL for the main list of stocks, now pointing to the class-based view
    path('', StockScreenerPageView.as_view(), name='grahams_table_list'),

    # URL for the detail page of a single stock
    path('stock/<str:symbol>/', StockDetailView.as_view(), name='stock_detail'),
]
