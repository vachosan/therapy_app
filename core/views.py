from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from accounts.forms import TherapistProfileForm
from accounts.models import TherapistProfile, User


class HomeView(TemplateView):
    template_name = "core/home.html"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"


class TherapistProfileEditView(LoginRequiredMixin, View):
    template_name = "core/therapist_profile_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role != User.Role.THERAPIST:
            raise PermissionDenied("Pouze terapeut může upravovat terapeutický profil.")
        return super().dispatch(request, *args, **kwargs)

    def get_profile(self):
        return TherapistProfile.objects.filter(user=self.request.user).first()

    def get(self, request, *args, **kwargs):
        profile = self.get_profile()
        initial = {}
        if profile is None:
            initial["display_name"] = request.user.get_full_name() or request.user.username
        form = TherapistProfileForm(instance=profile, initial=initial)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        profile = self.get_profile() or TherapistProfile(user=request.user)
        form = TherapistProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil terapeuta byl uložen.")
            return redirect("core:dashboard")
        return render(request, self.template_name, {"form": form})


class TherapistListView(ListView):
    context_object_name = "therapists"
    paginate_by = 12
    template_name = "core/therapist_list.html"

    def get_queryset(self):
        queryset = public_therapist_profiles()
        query = self.request.GET.get("q", "").strip()
        accepts_new_clients = self.request.GET.get("accepts_new_clients")

        if query:
            queryset = queryset.filter(
                Q(display_name__icontains=query)
                | Q(specialization__icontains=query)
                | Q(bio__icontains=query)
            )
        if accepts_new_clients == "1":
            queryset = queryset.filter(accepts_new_clients=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        context["accepts_new_clients"] = self.request.GET.get("accepts_new_clients") == "1"
        return context


class TherapistDetailView(DetailView):
    context_object_name = "therapist"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "core/therapist_detail.html"

    def get_queryset(self):
        return public_therapist_profiles()


def public_therapist_profiles():
    return TherapistProfile.objects.select_related("user").filter(
        user__role=User.Role.THERAPIST,
        is_verified=True,
    )
