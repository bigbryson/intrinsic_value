# /apps/dashboards/views.py
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from web_project import TemplateLayout
from django.contrib.auth.decorators import login_required
from apps.transactions.data_services import get_historical_portfolio_value
import json
from .data_services import get_market_movers
class DashboardsView(LoginRequiredMixin, TemplateView):
    login_url = '/accounts/auth/login/'
    template_name = 'dashboards/dashboard_analytics.html'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({"is_menu": True})

        has_connection = self.request.session.get('has_brokerage_connection', False)
        context['has_brokerage_connection'] = has_connection

        if has_connection:
            # Fetch the market movers data
            movers_data = get_market_movers(self.request.user)
            context.update(movers_data) # This adds top_gainers, top_losers, etc. to the context
        else:
            context['show_connection_prompt'] = True

        return context


# ... (keep the existing connection_page view) ...


# Add LoginRequiredMixin to the view
@login_required
def connection_page(request):
    """
    Renders the page that allows users to connect to their
    Schwab or E*TRADE accounts.
    """
    # We will use this exact path and filename
    return render(request, 'dashboards/connection_page.html')
class DashboardsView(LoginRequiredMixin, TemplateView):
    login_url = '/accounts/auth/login/'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({"is_menu": True})
        return context

@login_required
def connection_page(request):
    # If the user has already connected, send them to the dashboard.
    if request.session.get('has_brokerage_connection', False):
        return redirect('home')
    return render(request, 'dashboards/connection_page.html')
