from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework

from .models import Restaurant, RestaurantUserVote


class RestaurantHistoryFilter(rest_framework.FilterSet):
    restaurants = rest_framework.AllValuesMultipleFilter(field_name='id', label=_('restaurants'))
    date = rest_framework.DateFromToRangeFilter(field_name='created_datetime', label=_('date'))

    class Meta:
        model = Restaurant
        fields = ['restaurants', 'date']


class RestaurantWinnersHistoryFilter(rest_framework.FilterSet):
    restaurants = rest_framework.AllValuesMultipleFilter(field_name='restaurant_id', label=_('restaurants'))
    date = rest_framework.DateFromToRangeFilter(field_name='created_datetime', label=_('date'))

    class Meta:
        model = RestaurantUserVote
        fields = ['restaurants', 'date']
