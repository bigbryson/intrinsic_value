# /apps/authentication/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.views.generic import TemplateView
from web_project import TemplateLayout
from .forms import CustomUserCreationForm


class LoginView(TemplateView):
    template_name = 'authentication/auth_login_basic.html'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['form'] = AuthenticationForm()
        return context

    def post(self, request, *args, **kwargs):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('connection_page')

        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class RegisterView(TemplateView):
    template_name = 'authentication/auth_register_basic.html'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        # Use our new form here
        context['form'] = CustomUserCreationForm()
        return context

    def post(self, request, *args, **kwargs):
        # And also use it here for processing POST data
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('connection_page')

        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)

# Add this function back
def user_logout(request):
    logout(request)
    return redirect('authentication:auth-login-basic')

class AuthView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        # We can remove the layout override from here as well
        return context
