from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import TherapistProfile


User = get_user_model()


class CoreSmokeTests(TestCase):
    def test_placeholder(self):
        self.assertTrue(True)


class PublicTherapistCatalogTests(TestCase):
    def create_profile(
        self,
        username,
        display_name,
        role=None,
        is_verified=True,
        accepts_new_clients=True,
        specialization="Úzkosti",
        bio="Práce s dospělými klienty.",
    ):
        user = User.objects.create_user(
            username=username,
            password="StrongPass123",
            role=role or User.Role.THERAPIST,
        )
        return TherapistProfile.objects.create(
            user=user,
            display_name=display_name,
            specialization=specialization,
            bio=bio,
            accepts_new_clients=accepts_new_clients,
            is_verified=is_verified,
        )

    def test_public_list_is_available_without_login(self):
        response = self.client.get(reverse("core:therapist_list"))

        self.assertEqual(response.status_code, 200)

    def test_verified_therapist_is_visible(self):
        self.create_profile("verified", "Ověřený Terapeut")

        response = self.client.get(reverse("core:therapist_list"))

        self.assertContains(response, "Ověřený Terapeut")

    def test_unverified_therapist_is_not_visible(self):
        self.create_profile("unverified", "Neověřený Terapeut", is_verified=False)

        response = self.client.get(reverse("core:therapist_list"))

        self.assertNotContains(response, "Neověřený Terapeut")

    def test_profile_for_non_therapist_user_is_not_visible(self):
        user = User.objects.create_user(
            username="changed-role",
            password="StrongPass123",
            role=User.Role.THERAPIST,
        )
        profile = TherapistProfile.objects.create(
            user=user,
            display_name="Profil Bez Role Terapeuta",
            is_verified=True,
        )
        user.role = User.Role.CLIENT
        user.save()

        response = self.client.get(reverse("core:therapist_list"))

        self.assertNotContains(response, profile.display_name)

    def test_verified_therapist_detail_works(self):
        profile = self.create_profile("detail", "Detail Terapeuta")

        response = self.client.get(reverse("core:therapist_detail", args=[profile.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detail Terapeuta")
        self.assertContains(response, profile.bio)

    def test_unverified_therapist_detail_returns_404(self):
        profile = self.create_profile("private-detail", "Soukromý Terapeut", is_verified=False)

        response = self.client.get(reverse("core:therapist_detail", args=[profile.slug]))

        self.assertEqual(response.status_code, 404)

    def test_search_filters_results(self):
        self.create_profile(
            "trauma",
            "Trauma Terapeut",
            specialization="Trauma",
            bio="Somatická práce.",
        )
        self.create_profile(
            "family",
            "Rodinný Terapeut",
            specialization="Rodinná terapie",
            bio="Práce s páry.",
        )

        response = self.client.get(reverse("core:therapist_list"), {"q": "somatická"})

        self.assertContains(response, "Trauma Terapeut")
        self.assertNotContains(response, "Rodinný Terapeut")

    def test_accepts_new_clients_filter(self):
        self.create_profile("accepts", "Přijímá Klienty", accepts_new_clients=True)
        self.create_profile("closed", "Nepřijímá Klienty", accepts_new_clients=False)

        response = self.client.get(
            reverse("core:therapist_list"),
            {"accepts_new_clients": "1"},
        )

        self.assertContains(response, "Přijímá Klienty")
        self.assertNotContains(response, "Nepřijímá Klienty")

    def test_slug_is_unique_for_matching_display_names(self):
        first = self.create_profile("same-1", "Stejné Jméno")
        second = self.create_profile("same-2", "Stejné Jméno")

        self.assertEqual(first.slug, "stejne-jmeno")
        self.assertEqual(second.slug, "stejne-jmeno-2")

    def test_existing_slug_does_not_change_when_display_name_changes(self):
        profile = self.create_profile("stable-slug", "Původní Jméno")
        original_slug = profile.slug

        profile.display_name = "Nové Jméno"
        profile.save()

        self.assertEqual(profile.slug, original_slug)
