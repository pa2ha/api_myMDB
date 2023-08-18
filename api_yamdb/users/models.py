from django.contrib.auth.models import AbstractUser
from django.db import models

ROLE_CHOICES = (
    ('user', 'user'),
    ('moderator', 'moderator'),
    ('admin', 'admin'),
)


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=254,
        unique=True
    )
    bio = models.TextField(
        verbose_name='Биография',
        null=True,
        blank=True
    )
    role = models.CharField(
        verbose_name='Роль',
        max_length=20,
        choices=ROLE_CHOICES,
        blank=True,
        default='user'
    )
    confirmation_code = models.CharField(
        max_length=254,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ('username',)

    def __str__(self):
        return self.username
