from django.urls import path
from .views import goals_view

app_name = 'goals'
urlpatterns = [
    path('', goals_view, name='goals_view'),
]
