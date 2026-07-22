from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.models import TherapistProfile


class Command(BaseCommand):
    help = "Seed local development demo users and therapist profiles."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo_data is intended only for local development with DEBUG=True.")

        User = get_user_model()

        self._upsert_user(
            User,
            username="vacho",
            password="mullen",
            email="vacho@example.test",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        self._upsert_user(
            User,
            username="user",
            password="user",
            email="user@example.test",
            first_name="Testovací",
            last_name="Klient",
            role=User.Role.CLIENT,
        )
        therapist = self._upsert_user(
            User,
            username="therapist",
            password="user",
            email="therapist@example.test",
            first_name="Jana",
            last_name="Nováková",
            role=User.Role.THERAPIST,
        )
        unverified_therapist = self._upsert_user(
            User,
            username="therapist_unverified",
            password="user",
            email="therapist-unverified@example.test",
            first_name="Petr",
            last_name="Svoboda",
            role=User.Role.THERAPIST,
        )
        full_therapist = self._upsert_user(
            User,
            username="therapist_full",
            password="user",
            email="therapist-full@example.test",
            first_name="Eva",
            last_name="Malá",
            role=User.Role.THERAPIST,
        )

        self._upsert_profile(
            user=therapist,
            display_name="Mgr. Jana Nováková",
            specialization="Úzkosti, stres a partnerské vztahy",
            bio="Testovací profil ověřeného terapeuta určený pro ruční kontrolu veřejného katalogu.",
            accepts_new_clients=True,
            is_verified=True,
        )
        self._upsert_profile(
            user=unverified_therapist,
            display_name="Mgr. Petr Svoboda",
            specialization="Individuální terapie",
            bio="Tento profil je neověřený a nesmí se objevit ve veřejném katalogu.",
            accepts_new_clients=True,
            is_verified=False,
        )
        self._upsert_profile(
            user=full_therapist,
            display_name="PhDr. Eva Malá",
            specialization="Rodinná a párová terapie",
            bio="Ověřený testovací terapeut, který momentálně nepřijímá nové klienty.",
            accepts_new_clients=False,
            is_verified=True,
        )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))

    def _upsert_user(
        self,
        User,
        *,
        username,
        password,
        email,
        role,
        first_name="",
        last_name="",
        is_staff=False,
        is_superuser=False,
    ):
        user, _created = User.objects.get_or_create(username=username)
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.role = role
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.is_active = True
        user.set_password(password)
        user.save()
        return user

    def _upsert_profile(
        self,
        *,
        user,
        display_name,
        specialization,
        bio,
        accepts_new_clients,
        is_verified,
    ):
        profile = TherapistProfile.objects.filter(user=user).first()
        if profile is None:
            profile = TherapistProfile(user=user)
        profile.display_name = display_name
        profile.specialization = specialization
        profile.bio = bio
        profile.accepts_new_clients = accepts_new_clients
        profile.is_verified = is_verified
        profile.save()
        return profile
