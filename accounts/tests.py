from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


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
