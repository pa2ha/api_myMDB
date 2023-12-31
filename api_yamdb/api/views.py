from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Avg


from reviews.models import Category, Genre, Review, Title
from users.models import User
from .filters import TitleFilter
from .permissions import (IsAdmin,
                          IsSuperUserIsAdminIsModeratorIsAuthor,
                          IsSuperUserOrIsAdminOrReadOnly,
                          IsUserIsModeratorIsAdmin)
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, GetTokenSerializer,
                          ReadTitleSerializer, ReviewSerializer,
                          TitlesCreateSerializer, UserMeEditSerializer,
                          UserRegisterSerializer, UserSerializer)


class GenreViewSet(mixins.CreateModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet,
                   mixins.DestroyModelMixin):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    filter_backends = (filters.SearchFilter,)
    permission_classes = (IsSuperUserOrIsAdminOrReadOnly,)
    search_fields = ('name',)
    lookup_field = 'slug'


class CategoryViewSet(mixins.CreateModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet,
                      mixins.DestroyModelMixin):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = (filters.SearchFilter,)
    permission_classes = (IsSuperUserOrIsAdminOrReadOnly,)
    search_fields = ('name',)
    lookup_field = 'slug'


class TitlesViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all().annotate(rating=Avg(
        'reviews__score')).order_by('name')
    permission_classes = (IsSuperUserOrIsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter
    filterset_fields = ('year')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ReadTitleSerializer
        return TitlesCreateSerializer


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
        serializer.is_valid(raise_exception=True)
        if User.objects.filter(
                email=serializer.validated_data['email']).exists():
            return Response({'message': 'Такой email уже существует'},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['get', 'patch', ],
            detail=False,
            serializer_class=UserSerializer,
            permission_classes=(IsUserIsModeratorIsAdmin,))
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == 'PATCH':
            serializer = UserMeEditSerializer(user,
                                              data=request.data,
                                              partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)


def send_email(data, user):
    confirmation_code = default_token_generator.make_token(user)
    user.confirmation_code = confirmation_code
    user.save(update_fields=['confirmation_code'])
    return send_mail(
        subject="YaMDb - confirmation code",
        message=f"Your confirmation code: {confirmation_code}",
        from_email=None,
        recipient_list=[user.email],)


class UserRegister(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, _ = User.objects.get_or_create(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'])
        send_email(serializer.data, user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetTokenViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    def create(self, request):
        serializer = GetTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        confirmation_code = int(
            serializer.validated_data['confirmation_code'])
        user = get_object_or_404(User, username=username)
        if user.confirmation_code == confirmation_code:
            refresh = RefreshToken.for_user(user)
            token = {
                'token': str(refresh.access_token),
            }
            return Response(token, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Invalid confirmation code'},
                            status=status.HTTP_400_BAD_REQUEST)
