# /apps/authentication/urls.py
# /apps/authentication/urls.py
from django.urls import path
# Correctly import the new class-based views and the logout function
from .views import LoginView, RegisterView, user_logout, AuthView


urlpatterns = [
    # These URLs are already correct and point to the class-based views
    path("auth/login/", LoginView.as_view(), name="auth-login-basic"),
    path("auth/register/", RegisterView.as_view(), name="auth-register-basic"),

    # This URL for logout still correctly points to the logout function
    path("auth/logout/", user_logout, name="auth-logout-basic"),

    # This URL is also fine
    path(
        "auth/forgot_password/",
        AuthView.as_view(template_name='auth_forgot_password_basic.html'),
        name="auth-forgot-password-basic",
    ),
]
