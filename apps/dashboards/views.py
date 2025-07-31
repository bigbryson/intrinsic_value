# /apps/dashboards/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required


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
    # This tells the mixin where to redirect users if they are NOT logged in
    login_url = '/accounts/auth/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # You can add any extra context data for your template here
        # For example, let's pass the app name
        context['page_title'] = "Portfolio Dashboard"
        context.update({"is_menu": True})

        # Check the session to see if a connection has been made
        # If not, set a flag to show the modal.
        if not self.request.session.get('has_brokerage_connection', False):
            context['show_connection_modal'] = True
        return context
