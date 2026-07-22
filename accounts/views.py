from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import ClientRegistrationForm


class ClientRegistrationView(CreateView):
    form_class = ClientRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        messages.success(self.request, "Registrace byla dokončena. Nyní se můžete přihlásit.")
        return super().form_valid(form)
