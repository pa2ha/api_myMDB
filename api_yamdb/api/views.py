import random
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, viewsets, mixins, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .filters import TitleFilter


from .permissions import (IsAdmin, IsSuperUserIsAdminIsModeratorIsAuthor,
                          IsSuperUserOrIsAdminOnly, AnonimReadOnly, IsUserIsModeratorIsAdmin)
from .serializers import (TitlesSerializer, ReadTitleSerializer,
                          GenreSerializer, CategorySerializer,
                          UserSerializer, UserRegisterSerializer,
                          ReviewSerializer, CommentSerializer,
                          GetTokenSerializer)
from reviews.models import Titles, Genre, Category, Review
from users.models import User


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
    queryset = Titles.objects.all()
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
    """Вьюсет для обьектов модели Review."""

    serializer_class = ReviewSerializer
    permission_classes = (
        IsSuperUserIsAdminIsModeratorIsAuthor,
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
    permission_classes = (IsAdmin,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    lookup_field = 'username'

    def create(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.initial_data['username']=='me':
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
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
            serializer = self.get_serializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_200_OK)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class UserRegister(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        try:
            username = serializer.initial_data['username']
            email = serializer.initial_data['email']
        except KeyError as e:
            return Response({'error': f'Missing key: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username, email=email).exists():
            user = User.objects.get(username=username)
            send_mail(
                subject="YaMDb - confirmation code",
                message=f"Your confirmation code: {user.confirmation_code}",
                from_email=None,
                recipient_list=[user.email],
             )
            return Response(serializer.initial_data, status=status.HTTP_200_OK)
        if serializer.is_valid():
            serializer.save()
            user = User.objects.get(
                username=serializer.validated_data['username'])
            confirmation_code = random.randint(111111, 999999)
            user.confirmation_code = confirmation_code
            user.save(update_fields=['confirmation_code'])
            send_mail(
                subject="YaMDb - confirmation code",
                message=f"Your confirmation code: {confirmation_code}",
                from_email=None,
                recipient_list=[user.email],)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetTokenViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    def create(self, request):
        serializer = GetTokenSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            confirmation_code = int(
                serializer.validated_data['confirmation_code'])
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
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class CommentViewSet(viewsets.ModelViewSet):
    """Вьюсет для обьектов модели Comment."""

    serializer_class = CommentSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly,
        IsSuperUserIsAdminIsModeratorIsAuthor
    )

    def get_review(self):
        """Возвращает объект текущего отзыва."""
        review_id = self.kwargs.get('review_id')
        return get_object_or_404(Review, pk=review_id)

    def get_queryset(self):
        """Возвращает queryset c комментариями для текущего отзыва."""
        return self.get_review().comments.all()

    def perform_create(self, serializer):
        """Создает комментарий для текущего отзыва,
        где автором является текущий пользователь."""
        serializer.save(
            author=self.request.user,
            review=self.get_review()
        )
