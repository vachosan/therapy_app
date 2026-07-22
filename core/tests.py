from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from accounts.forms import TherapistProfileForm
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


class TherapistProfileEditTests(TestCase):
    def test_profile_form_contains_only_public_editable_fields(self):
        form = TherapistProfileForm()

        self.assertEqual(
            list(form.fields),
            ["display_name", "specialization", "bio", "accepts_new_clients"],
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("core:therapist_profile_edit"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('core:therapist_profile_edit')}",
        )

    def test_opening_empty_profile_form_does_not_create_profile(self):
        user = User.objects.create_user(
            username="empty-therapist",
            password="StrongPass123",
            role=User.Role.THERAPIST,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:therapist_profile_edit"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(TherapistProfile.objects.filter(user=user).exists())

    def test_therapist_can_create_own_profile(self):
        user = User.objects.create_user(
            username="new-therapist",
            password="StrongPass123",
            role=User.Role.THERAPIST,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("core:therapist_profile_edit"),
            {
                "display_name": "Mgr. Nový Terapeut",
                "specialization": "Úzkosti",
                "bio": "Práce s dospělými klienty.",
                "accepts_new_clients": "on",
            },
        )

        self.assertRedirects(response, reverse("core:dashboard"))
        profile = TherapistProfile.objects.get(user=user)
        self.assertEqual(profile.display_name, "Mgr. Nový Terapeut")
        self.assertEqual(profile.specialization, "Úzkosti")
        self.assertTrue(profile.accepts_new_clients)
        self.assertFalse(profile.is_verified)

    def test_therapist_can_update_own_profile(self):
        user = User.objects.create_user(
            username="edit-therapist",
            password="StrongPass123",
            role=User.Role.THERAPIST,
        )
        profile = TherapistProfile.objects.create(
            user=user,
            display_name="Původní Terapeut",
            is_verified=True,
        )
        self.client.force_login(profile.user)

        response = self.client.post(
            reverse("core:therapist_profile_edit"),
            {
                "display_name": "Upravený Terapeut",
                "specialization": "Trauma",
                "bio": "Aktualizované bio.",
            },
        )

        self.assertRedirects(response, reverse("core:dashboard"))
        profile.refresh_from_db()
        self.assertEqual(profile.display_name, "Upravený Terapeut")
        self.assertEqual(profile.specialization, "Trauma")
        self.assertFalse(profile.accepts_new_clients)

    def test_client_cannot_edit_therapist_profile(self):
        user = User.objects.create_user(
            username="client-no-profile-edit",
            password="StrongPass123",
            role=User.Role.CLIENT,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:therapist_profile_edit"))

        self.assertEqual(response.status_code, 403)

    def test_admin_cannot_edit_therapist_profile(self):
        user = User.objects.create_user(
            username="admin-no-profile-edit",
            password="StrongPass123",
            role=User.Role.ADMIN,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:therapist_profile_edit"))

        self.assertEqual(response.status_code, 403)

    def test_profile_edit_does_not_accept_verified_flag(self):
        user = User.objects.create_user(
            username="self-verify",
            password="StrongPass123",
            role=User.Role.THERAPIST,
        )
        self.client.force_login(user)

        self.client.post(
            reverse("core:therapist_profile_edit"),
            {
                "display_name": "Self Verify",
                "specialization": "Koučink",
                "bio": "Text profilu.",
                "accepts_new_clients": "on",
                "is_verified": "on",
            },
        )

        self.assertFalse(TherapistProfile.objects.get(user=user).is_verified)

    def test_profile_edit_does_not_accept_user_or_slug(self):
        owner = User.objects.create_user(
            username="profile-owner",
            password="StrongPass123",
            role=User.Role.THERAPIST,
        )
        other = User.objects.create_user(
            username="profile-other",
            password="StrongPass123",
            role=User.Role.THERAPIST,
        )
        self.client.force_login(owner)

        self.client.post(
            reverse("core:therapist_profile_edit"),
            {
                "display_name": "Owner Profile",
                "specialization": "Rodinná terapie",
                "bio": "Text profilu.",
                "accepts_new_clients": "on",
                "user": str(other.pk),
                "slug": "podvrzeny-slug",
            },
        )

        profile = TherapistProfile.objects.get(user=owner)
        self.assertEqual(profile.user, owner)
        self.assertEqual(profile.slug, "owner-profile")
        self.assertFalse(TherapistProfile.objects.filter(user=other).exists())

    def test_therapist_cannot_update_another_therapist_profile(self):
        owner = User.objects.create_user(
            username="own-profile",
            password="StrongPass123",
            role=User.Role.THERAPIST,
        )
        other = User.objects.create_user(
            username="foreign-profile",
            password="StrongPass123",
            role=User.Role.THERAPIST,
        )
        own_profile = TherapistProfile.objects.create(
            user=owner,
            display_name="Vlastní Profil",
        )
        other_profile = TherapistProfile.objects.create(
            user=other,
            display_name="Cizí Profil",
        )
        self.client.force_login(owner)

        response = self.client.post(
            reverse("core:therapist_profile_edit"),
            {
                "display_name": "Upravený Vlastní Profil",
                "specialization": "Trauma",
                "bio": "Vlastní text.",
                "user": str(other.pk),
                "slug": other_profile.slug,
            },
        )

        self.assertRedirects(response, reverse("core:dashboard"))
        own_profile.refresh_from_db()
        other_profile.refresh_from_db()
        self.assertEqual(own_profile.display_name, "Upravený Vlastní Profil")
        self.assertEqual(own_profile.user, owner)
        self.assertEqual(other_profile.display_name, "Cizí Profil")
        self.assertEqual(other_profile.user, other)

    def test_profile_edit_does_not_change_user_role(self):
        user = User.objects.create_user(
            username="role-spoof",
            password="StrongPass123",
            role=User.Role.THERAPIST,
        )
        self.client.force_login(user)

        self.client.post(
            reverse("core:therapist_profile_edit"),
            {
                "display_name": "Role Spoof",
                "specialization": "Koučink",
                "bio": "Text profilu.",
                "role": User.Role.ADMIN,
            },
        )

        user.refresh_from_db()
        self.assertEqual(user.role, User.Role.THERAPIST)

    def test_display_name_change_does_not_change_existing_slug(self):
        user = User.objects.create_user(
            username="profile-slug-stable",
            password="StrongPass123",
            role=User.Role.THERAPIST,
        )
        profile = TherapistProfile.objects.create(
            user=user,
            display_name="Původní Jméno",
        )
        original_slug = profile.slug
        self.client.force_login(user)

        self.client.post(
            reverse("core:therapist_profile_edit"),
            {
                "display_name": "Nové Jméno",
                "specialization": "Trauma",
                "bio": "Aktualizované bio.",
            },
        )

        profile.refresh_from_db()
        self.assertEqual(profile.slug, original_slug)

    def test_successful_save_shows_expected_dashboard_result_and_message(self):
        user = User.objects.create_user(
            username="success-result",
            password="StrongPass123",
            role=User.Role.THERAPIST,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("core:therapist_profile_edit"),
            {
                "display_name": "Výsledek Uložení",
                "specialization": "Úzkosti",
                "bio": "Text profilu.",
                "accepts_new_clients": "on",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("core:dashboard"))
        self.assertContains(response, "Výsledek Uložení")
        self.assertContains(response, "Profil terapeuta byl uložen.")
        self.assertIn(
            "Profil terapeuta byl uložen.",
            [str(message) for message in get_messages(response.wsgi_request)],
        )
