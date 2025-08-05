from django.urls import path
from .views import savings_view

app_name = 'savings'
urlpatterns = [
    path('', savings_view, name='savings_view'),
]
