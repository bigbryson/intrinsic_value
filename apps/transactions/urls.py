from django.urls import path
from .views import transactions_list

app_name = 'transactions'
urlpatterns = [
    path('', transactions_list, name='transactions_list'),
]
