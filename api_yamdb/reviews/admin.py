from django.contrib import admin

from .models import Title, Genre, Category

# Register your models here.
admin.site.register(Title)
admin.site.register(Genre)
admin.site.register(Category)
