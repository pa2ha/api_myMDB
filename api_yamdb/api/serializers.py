from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from reviews.models import Category, Comment, Genre, Review, Title
from users.models import User
from .validators import validate_username


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('name', 'slug')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'slug')


class TitlesCreateSerializer(serializers.ModelSerializer):

    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True
    )
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all(),)

    class Meta:
        model = Title
        fields = '__all__'


class ReadTitleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(read_only=True, many=True)
    rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Title
        fields = "__all__"


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(
        read_only=True
    )

    class Meta:
        model = Review
        fields = (
            'id', 'text', 'author', 'score', 'pub_date')

    def validate(self, data):
        if not self.context.get('request').method == 'POST':
            return data
        author = self.context.get('request').user
        title_id = self.context.get('view').kwargs.get('title_id')
        if Review.objects.filter(author=author, title=title_id).exists():
            raise serializers.ValidationError(
                'Вы уже оставляли отзыв на это произведение'
            )
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(
        read_only=True
    )

    class Meta:
        model = Comment
        fields = (
            'id', 'text', 'author', 'pub_date')


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150,
                                     required=True,
                                     validators=[
                                         RegexValidator(
                                             regex='^[a-zA-Z0-9_]*$'),
                                         UniqueValidator(
                                             queryset=User.objects.all()),
                                         validate_username
                                     ],
                                     )
    email = serializers.EmailField(max_length=254, required=True)

    class Meta:
        fields = ('username', 'email', 'first_name',
                  'last_name', 'bio', 'role')
        model = User


class UserRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150,
                                     required=True,
                                     validators=[
                                         RegexValidator(
                                             regex='^[a-zA-Z0-9_]*$'),
                                         validate_username])
    email = serializers.EmailField(max_length=254,
                                   required=True)

    class Meta:
        fields = ('email', 'username')
        model = User

    def validate(self, data):
        if not User.objects.filter(username=data.get('username'),
                                   email=data.get('email')):
            if User.objects.filter(email=data.get('email')):
                raise serializers.ValidationError(
                    'Пользователь с таким email уже существует'
                )
            if User.objects.filter(username=data.get('username')):
                raise serializers.ValidationError(
                    'Пользователь с таким именем уже существует'
                )
        return data


class UserMeEditSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150,
                                     validators=[
                                         RegexValidator(
                                             regex='^[a-zA-Z0-9_]*$')])
    email = serializers.EmailField(max_length=254)

    class Meta:
        fields = ('username', 'email', 'first_name',
                  'last_name', 'bio')
        model = User


class GetTokenSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    confirmation_code = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('username', 'confirmation_code')
