from django.contrib.auth.models import AbstractUser
from django.db import models
from enum import Enum


class RoleChoice(Enum):
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'


class User(AbstractUser):
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=150,
        unique=True
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=254,
        unique=True,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
        null=True
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
    )
    bio = models.TextField(
        verbose_name='Биография',
        null=True,
        blank=True
    )
    role = models.CharField(
        verbose_name='Роль',
        max_length=20,
        choices=[(role, role.value) for role in RoleChoice],
        default=RoleChoice.USER
    )


