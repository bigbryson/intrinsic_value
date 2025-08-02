# /apps/connection_page/urls.py
from django.urls import path
from . import views

app_name = 'connection_page'

urlpatterns = [
    path('yodlee/launch-fastlink/', views.generate_fastlink_token, name='yodlee_launch_fastlink'),
    # Add this new URL for the success callback
    path('yodlee/success-callback/', views.yodlee_success_callback, name='yodlee_success_callback'),
]

