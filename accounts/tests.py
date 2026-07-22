from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import TherapistProfile


User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user_with_role(self):
        user = User.objects.create_user(
            username="client1",
            email="client@example.com",
            password="StrongPass123",
            role=User.Role.CLIENT,
        )

        self.assertEqual(user.role, User.Role.CLIENT)
        self.assertTrue(user.check_password("StrongPass123"))


class AuthFlowTests(TestCase):
    def test_client_registration_creates_client_user(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newclient",
                "email": "newclient@example.com",
                "first_name": "New",
                "last_name": "Client",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
            },
        )

        self.assertRedirects(response, reverse("accounts:login"))
        user = User.objects.get(username="newclient")
        self.assertEqual(user.role, User.Role.CLIENT)

    def test_client_registration_ignores_submitted_role(self):
        attempted_roles = [User.Role.THERAPIST, User.Role.ADMIN]

        for attempted_role in attempted_roles:
            with self.subTest(attempted_role=attempted_role):
                username = f"client-{attempted_role}"
                response = self.client.post(
                    reverse("accounts:register"),
                    {
                        "username": username,
                        "email": f"{username}@example.com",
                        "first_name": "Role",
                        "last_name": "Spoof",
                        "password1": "StrongPass123",
                        "password2": "StrongPass123",
                        "role": attempted_role,
                    },
                )

                self.assertRedirects(response, reverse("accounts:login"))
                user = User.objects.get(username=username)
                self.assertEqual(user.role, User.Role.CLIENT)

    def test_login(self):
        User.objects.create_user(username="client1", password="StrongPass123")

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "client1", "password": "StrongPass123"},
        )

        self.assertRedirects(response, reverse("core:dashboard"))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("core:dashboard"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('core:dashboard')}",
        )


class TherapistProfileTests(TestCase):
    def test_client_cannot_have_valid_therapist_profile(self):
        user = User.objects.create_user(
            username="client-profile",
            password="StrongPass123",
            role=User.Role.CLIENT,
        )
        profile = TherapistProfile(user=user, display_name="Client Profile")

        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_therapist_can_have_therapist_profile(self):
        user = User.objects.create_user(
            username="therapist-profile",
            password="StrongPass123",
            role=User.Role.THERAPIST,
        )
        profile = TherapistProfile.objects.create(
            user=user,
            display_name="Terapeut Test",
            specialization="Úzkosti",
        )

        self.assertEqual(profile.user, user)
        self.assertEqual(profile.specialization, "Úzkosti")

    def test_admin_role_cannot_have_valid_therapist_profile(self):
        user = User.objects.create_user(
            username="admin-profile",
            password="StrongPass123",
            role=User.Role.ADMIN,
        )
        profile = TherapistProfile(user=user, display_name="Admin Profile")

        with self.assertRaises(ValidationError):
            profile.full_clean()


class DashboardTests(TestCase):
    def test_client_sees_client_dashboard(self):
        user = User.objects.create_user(
            username="uzivatel1",
            password="StrongPass123",
            role=User.Role.CLIENT,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:dashboard"))

        self.assertContains(response, "Klientský dashboard")
        self.assertContains(response, "Role účtu: Klient")

    def test_therapist_sees_therapist_dashboard(self):
        user = User.objects.create_user(
            username="terapeut1",
            password="StrongPass123",
            role=User.Role.THERAPIST,
        )
        TherapistProfile.objects.create(
            user=user,
            display_name="Terapeut Test",
            specialization="Rodinná terapie",
            is_verified=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:dashboard"))

        self.assertContains(response, "Terapeutský dashboard")
        self.assertContains(response, "Role účtu: Terapeut")
        self.assertContains(response, "Terapeut Test")
        self.assertContains(response, "Rodinná terapie")
        self.assertContains(response, "Ověřený profil")
        self.assertContains(response, "Přijímá nové klienty")

    def test_therapist_without_profile_sees_missing_profile_message(self):
        user = User.objects.create_user(
            username="terapeut2",
            password="StrongPass123",
            role=User.Role.THERAPIST,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:dashboard"))

        self.assertContains(response, "Terapeutský dashboard")
        self.assertContains(response, "Profil terapeuta zatím nebyl vytvořen.")

    def test_admin_sees_admin_dashboard(self):
        user = User.objects.create_user(
            username="spravce1",
            password="StrongPass123",
            role=User.Role.ADMIN,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:dashboard"))

        self.assertContains(response, "Administrátorský dashboard")
        self.assertContains(response, "Role účtu: Administrátor")

    def test_dashboard_shows_czech_role_name_instead_of_internal_value(self):
        user = User.objects.create_user(
            username="bezroletextu",
            password="StrongPass123",
            role=User.Role.CLIENT,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:dashboard"))
        content = response.content.decode()

        self.assertIn("Role účtu: Klient", content)
        self.assertNotIn("Role účtu: client", content)
