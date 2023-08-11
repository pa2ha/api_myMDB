from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q

CHOICES = (
    ('user', 'user'),
    ('moderator', 'moderator'),
    ('admin', 'admin'),
)


class User(AbstractUser):
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=150,
        unique=True
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=254,
        unique=True
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
        null=True,
        blank=True
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
        null=True,
        blank=True
    )
    bio = models.TextField(
        verbose_name='Биография',
        null=True,
        blank=True
    )
    role = models.CharField(
        verbose_name='Роль',
        max_length=20,
        choices=CHOICES,
        blank=True,
        default='user'
    )
    confirmation_code = models.IntegerField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ('username',)
        constraints = (
            models.CheckConstraint(
                check=~Q(username__iexact='me'),
                name='username_not_me'
            ),
        )

    def __str__(self):
        return self.username
