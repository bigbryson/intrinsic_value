from django.urls import path
from .views import DashboardsView, connection_page



urlpatterns = [
 path(
        "",
        DashboardsView.as_view(template_name="dashboard_analytics.html"),
        name="index",
    ),
    # Add this second path pointing to the same view, but named 'home'
    # This will fix the redirect from the login page.
    path(
        "home/",
        DashboardsView.as_view(template_name="dashboard_analytics.html"),
        name="home",
    ),
    path('connect/', connection_page, name='connection_page'),
]
