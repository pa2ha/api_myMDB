import csv

from django.core.management.base import BaseCommand

from reviews.models import Category, Comment, Genre, GenreTitle, Review, Title
from users.models import User

csv_files = ["category.csv", "genre.csv", "titles.csv", "genre_title.csv",
             "users.csv", "review.csv", "comments.csv"]

csv_fields = {"category.csv": ["id", "name", "slug"],
              "genre_title.csv": ["id", "title_id", "genre_id"],
              "genre.csv": ["id", "name", "slug"],
              "review.csv": ["id", "title_id", "text", "author",
                             "score", "pub_date"],
              "titles.csv": ["id", "name", "year", "category"],
              "users.csv": ["id", "username", "email", "role", "bio",
                            "first_name", "last_name"],
              "comments.csv": ["id", "review_id", "text", "author", "pub_date"]
              }

Models = {"category": Category,
          "genre": Genre,
          "genre_title": GenreTitle,
          "review": Review,
          "titles": Title,
          "users": User,
          "comments": Comment}


def csv_reader_file(csv_file_name):
    csv_file_path = "static/data/" + csv_file_name
    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        csvreader = csv.DictReader(csvfile)
        return list(csvreader)


class Command(BaseCommand):

    def handle(self, *args, **options):
        for csv_file_name in csv_files:
            for row in csv_reader_file(csv_file_name):
                model = csv_file_name.split('.')[0]
                model_class = Models.get(model)
                item = None
                if model_class == Category:
                    item = Category(
                        id=row["id"],
                        name=row["name"],
                        slug=row["slug"])
                elif model_class == Genre:
                    item = Genre(
                        id=row["id"],
                        name=row["name"],
                        slug=row["slug"])
                elif model_class == Title:
                    category_id = int(row["category"])
                    category_instance = Category.objects.get(pk=category_id)
                    item = Title(
                        name=row["name"],
                        year=int(row["year"]),
                        category=category_instance
                    )
                elif model_class == GenreTitle:
                    genre_id = int(row["genre_id"])
                    genre_instance = Genre.objects.get(pk=genre_id)
                    title_id = int(row["title_id"])
                    title_instance = Title.objects.get(pk=title_id)
                    item = GenreTitle.objects.create(
                        genre=genre_instance,
                        title_id=title_instance.id)
                elif model_class == User:
                    item = User(
                        id=int(row["id"]),
                        username=row["username"],
                        email=row["email"],
                        role=row["role"],
                        bio=row["bio"],
                        first_name=row["first_name"],
                        last_name=row["last_name"]
                    )
                elif model_class == Review:
                    author_id = int(row["author"])
                    author_instanse = User.objects.get(pk=author_id)
                    title_id = int(row["title_id"])
                    title_instance = Title.objects.get(pk=title_id)
                    item = Review(
                        id=int(row["id"]),
                        title=title_instance,
                        text=row["text"],
                        author=author_instanse,
                        score=int(row["score"]),
                        pub_date=row["pub_date"]
                    )
                elif model_class == Comment:
                    author_id = int(row["author"])
                    author_instanse = User.objects.get(pk=author_id)
                    review_id = int(row["review_id"])
                    review_instance = Review.objects.get(pk=review_id)
                    item = Comment(
                        id=int(row["id"]),
                        review=review_instance,
                        text=row["text"],
                        author=author_instanse,
                        pub_date=row["pub_date"]
                    )
                else:
                    self.stdout.write(self.style.ERROR(
                        f"Не удалось создать объект для модели {model}"))
                    continue
                item.full_clean()
                item.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Запись для модели {model} успешно добавлена: {row}"))
