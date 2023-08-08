from django.contrib import admin

from .models import Titles, Genre, Category

# Register your models here.
admin.site.register(Titles)
admin.site.register(Genre)
admin.site.register(Category)
