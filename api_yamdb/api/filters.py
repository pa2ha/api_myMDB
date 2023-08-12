from django_filters import rest_framework as filters

from reviews.models import Titles


class TitleFilter(filters.FilterSet):

    category = filters.CharFilter(
        field_name='category__slug',
    )
    genre = filters.CharFilter(
        field_name='genre__slug',
    )
    year = filters.NumberFilter(
        field_name="year",
        lookup_expr='exact'
    )
    name = filters.CharFilter(
        field_name='name',
    )

    class Meta:
        model = Titles
        fields = ('category', 'genre', 'name', 'year')
