from django.contrib import admin

from .models import Category, Genre, Title

# Register your models here.
admin.site.register(Title)
admin.site.register(Genre)
admin.site.register(Category)
