from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TitlesViewSet, GenreViewSet, CategoryViewSet, UserViewSet, ReviewViewSet


v1_router = DefaultRouter()
v1_router.register('titles', TitlesViewSet)
v1_router.register('genres', GenreViewSet)
v1_router.register('categories', CategoryViewSet)
v1_router.register(
    r'titles/(?P<title_id>\d+)/reviews', ReviewViewSet, basename='reviews'
)
v1_router.register('users', UserViewSet)


urlpatterns = [
    path('v1/', include(v1_router.urls)),
    path('v1/auth/signup/', name='register'),
]
