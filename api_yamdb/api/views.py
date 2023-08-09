from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, viewsets, mixins, status
from rest_framework.permissions import SAFE_METHODS
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Avg

from .permissions import IsSuperUserIsAdminIsModeratorIsAuthor
from .serializers import (TitlesSerializer, ReadTitleSerializer, GenreSerializer,
                          CategorySerializer, UserSerializer, ReviewSerializer)
from reviews.models import Titles, Genre, Category, Review
from users.models import User


class GenreViewSet(mixins.CreateModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet,
                   mixins.DestroyModelMixin):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class CategoryViewSet(mixins.CreateModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet,
                      mixins.DestroyModelMixin):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class TitlesViewSet(viewsets.ModelViewSet):
    queryset = Titles.objects.annotate(rating=Avg('reviews__score')).all()
    serializer_class = TitlesSerializer

    def perform_create(self, serializer):
        genre_names = self.request.data.get('genre', [])
        existing_genres = Genre.objects.filter(name__in=genre_names)
        if existing_genres.count() == len(genre_names):
            serializer.save()
        else:
            raise ValidationError("Указаны несуществующие жанры")

    def get_serializer_class(self):
        if self.action in SAFE_METHODS:
            return ReadTitleSerializer
        return TitlesSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """Вьюсет для обьектов модели Review."""

    serializer_class = ReviewSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly,
        IsSuperUserIsAdminIsModeratorIsAuthor
    )

    def get_title(self):
        """Возвращает объект текущего произведения."""
        title_id = self.kwargs.get('title_id')
        return get_object_or_404(Titles, pk=title_id)

    def get_queryset(self):
        """Возвращает queryset c отзывами для текущего произведения."""
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        """Создает отзыв для текущего произведения,
        где автором является текущий пользователь."""
        serializer.save(
            author=self.request.user,
            title=self.get_title()
        )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter)
    search_fields = ('username',)
    lookup_field = 'username'

    @action(methods=['get', 'patch',],
            detail=False,
            url_path='me',
            serializer_class=UserSerializer)
    def user_profile(self, request):
        user = request.user
        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == "PATCH":
            serializer = self.get_serializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
