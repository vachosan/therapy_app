from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = "client", "Klient"
        THERAPIST = "therapist", "Terapeut"
        ADMIN = "admin", "Administrátor"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
    )


class TherapistProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="therapist_profile",
    )
    display_name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    bio = models.TextField(blank=True)
    specialization = models.CharField(max_length=150, blank=True)
    accepts_new_clients = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name

    def _generate_unique_slug(self):
        base_slug = slugify(self.display_name) or "terapeut"
        slug = base_slug
        index = 2
        while TherapistProfile.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{index}"
            index += 1
        return slug

    def clean(self):
        super().clean()
        if self.user_id and self.user.role != User.Role.THERAPIST:
            raise ValidationError(
                {"user": "Profil terapeuta smí patřit pouze uživateli s rolí terapeut."}
            )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        self.full_clean()
        return super().save(*args, **kwargs)
