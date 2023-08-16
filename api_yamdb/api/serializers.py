from django.core.validators import RegexValidator
from django.db.models import Avg
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from reviews.models import Category, Comment, Genre, Review, Title
from users.models import CHOICES, User
from .validators import validate_username


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('name', 'slug')

    def validate_slug(self, value):
        if Genre.objects.filter(slug=value).exists():
            raise serializers.ValidationError(
                "Жанр с таким слагом уже существует"
            )
        return value


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'slug')

    def validate_slug(self, value):
        if Category.objects.filter(slug=value).exists():
            raise serializers.ValidationError(
                "Категория с таким слагом уже существует"
            )
        return value


class TitlesSerializer(serializers.ModelSerializer):

    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True
    )
    rating = serializers.SerializerMethodField()
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all(),)

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'rating',
                  'description', 'genre', 'category')

    def get_rating(self, obj):
        average_score = Review.objects.filter(title=obj).aggregate(
            Avg('score'))['score__avg']
        return average_score


class ReadTitleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(read_only=True, many=True)
    rating = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Title
        fields = "__all__"

    def get_rating(self, obj):
        average_score = Review.objects.filter(title=obj).aggregate(
            Avg('score'))['score__avg']
        return average_score


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
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    role = serializers.ChoiceField(choices=CHOICES, required=False)

    class Meta:
        fields = ('username', 'email', 'first_name',
                  'last_name', 'bio', 'role')
        model = User


class UserRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150,
                                     required=True,
                                     validators=[
                                         RegexValidator(
                                             regex='^[a-zA-Z0-9_]*$'),
                                         UniqueValidator(
                                             queryset=User.objects.all()),
                                         validate_username])
    email = serializers.EmailField(max_length=254,
                                   required=True,
                                   validators=[
                                       UniqueValidator(
                                           queryset=User.objects.all()
                                       ),
                                   ])

    class Meta:
        fields = ('email', 'username')
        model = User
        validators = [
            UniqueTogetherValidator(
                queryset=User.objects.all(),
                fields=['username', 'email']
            )
        ]


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