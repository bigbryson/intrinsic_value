from django.urls import path
from .views import financials_view

app_name = 'financials'
urlpatterns = [
    path('', financials_view, name='financials_view'),
]
