from django.urls import path

from .views import DashboardView, HomeView, TherapistDetailView, TherapistListView


app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("therapists/", TherapistListView.as_view(), name="therapist_list"),
    path("therapists/<slug:slug>/", TherapistDetailView.as_view(), name="therapist_detail"),
]
