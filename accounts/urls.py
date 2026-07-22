from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .forms import BootstrapAuthenticationForm
from .views import ClientRegistrationView


app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=BootstrapAuthenticationForm,
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", ClientRegistrationView.as_view(), name="register"),
]
