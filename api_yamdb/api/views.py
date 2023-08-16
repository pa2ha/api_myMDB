import random

from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from reviews.models import Category, Genre, Review, Title
from users.models import User
from .filters import TitleFilter
from .permissions import (AnonimReadOnly, IsAdmin,
                          IsSuperUserIsAdminIsModeratorIsAuthor,
                          IsSuperUserOrIsAdminOnly, IsUserIsModeratorIsAdmin)
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, GetTokenSerializer,
                          ReadTitleSerializer, ReviewSerializer,
                          TitlesSerializer, UserMeEditSerializer,
                          UserRegisterSerializer, UserSerializer)


class GenreViewSet(mixins.CreateModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet,
                   mixins.DestroyModelMixin):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    filter_backends = (filters.SearchFilter,)
    permission_classes = (IsSuperUserOrIsAdminOnly,)
    search_fields = ('name',)
    lookup_field = 'slug'

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return super().get_permissions()


class CategoryViewSet(mixins.CreateModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet,
                      mixins.DestroyModelMixin):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = (filters.SearchFilter,)
    permission_classes = (IsSuperUserOrIsAdminOnly,)
    search_fields = ('name',)
    lookup_field = 'slug'

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return super().get_permissions()


class TitlesViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitlesSerializer
    permission_classes = (AnonimReadOnly | IsSuperUserOrIsAdminOnly,)
    response_serializer_class = ReadTitleSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def perform_create(self, serializer):
        genre_names = self.request.data.get('slug', [])
        existing_genres = Genre.objects.filter(slug__in=genre_names)
        if existing_genres.count() == len(genre_names):
            instance = serializer.save()
            response_serializer = self.response_serializer_class(instance)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        else:
            raise ValidationError("Указаны несуществующие жанры")

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ReadTitleSerializer
        return TitlesSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return super().get_permissions()


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (
        IsSuperUserIsAdminIsModeratorIsAuthor,
        permissions.IsAuthenticatedOrReadOnly
    )

    def get_title(self):
        title_id = self.kwargs.get('title_id')
        return get_object_or_404(Title, pk=title_id)

    def get_queryset(self):
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            title=self.get_title()
        )


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly,
        IsSuperUserIsAdminIsModeratorIsAuthor
    )

    def get_review(self):
        review_id = self.kwargs.get('review_id')
        return get_object_or_404(Review, pk=review_id)

    def get_queryset(self):
        return self.get_review().comments.all()

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            review=self.get_review()
        )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdmin,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    lookup_field = 'username'

    def create(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            if (serializer.initial_data['username'] == 'me'
                or User.objects.filter(
                    email=serializer.validated_data['email']).exists()):
                return Response({'message': 'Invalid username'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get', 'patch', ],
            detail=False,
            url_path='me',
            serializer_class=UserSerializer,
            permission_classes=(IsUserIsModeratorIsAdmin,))
    def user_profile(self, request):
        user = request.user
        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == "PATCH":
            serializer = UserMeEditSerializer(user,
                                              data=request.data,
                                              partial=True)
            if serializer.is_valid():
                try:
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                except IntegrityError:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


def send_email(data, user):
    confirmation_code = random.randint(111111, 999999)
    user.confirmation_code = confirmation_code
    user.save(update_fields=['confirmation_code'])
    send_mail(
        subject="YaMDb - confirmation code",
        message=f"Your confirmation code: {confirmation_code}",
        from_email=None,
        recipient_list=[user.email],)
    return Response(data, status=status.HTTP_200_OK)


class UserRegister(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        try:
            username = serializer.initial_data['username']
            email = serializer.initial_data['email']
        except KeyError:
            if not serializer.is_valid():
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username, email=email).exists():
            user = User.objects.get(username=username)
            return send_email(serializer.initial_data, user)
        if serializer.is_valid():
            serializer.save()
            user = User.objects.get(
                username=serializer.validated_data['username'])
            return send_email(serializer.data, user)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetTokenViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    def create(self, request):
        serializer = GetTokenSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            confirmation_code = int(
                serializer.validated_data['confirmation_code'])
            try:
                user = User.objects.get(username=username)
                if user.confirmation_code == confirmation_code:
                    refresh = RefreshToken.for_user(user)
                    token = {
                        'token': str(refresh.access_token),
                    }
                    return Response(token, status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'Invalid confirmation code'},
                                    status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
