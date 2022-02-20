from django.test import TestCase
from django.utils.translation import gettext as _

from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory

from restaurants.models import Restaurant, RestaurantUserVote
from restaurants.serializers import RestaurantsListSerializer, RestaurantUserVoteSerializer
from users.models import User


class RestaurantsListSerializerShould(TestCase):
    def test_return_vote_url_field_with_restaurant_vote_url(self):
        restaurant = Restaurant.objects.create(title='TestTitle', address='TestAddress')
        serializer = RestaurantsListSerializer(restaurant)

        self.assertURLEqual(serializer.data.get('vote_url'), reverse('restaurant_vote', kwargs={'pk': restaurant.pk}))


class RestaurantUserVoteSerializerShould(TestCase):
    def setUp(self):
        self.error_message = _('You already voted maximum times allowed for this restaurant today')
        self.user = User.objects.create_user(username='u', daily_vote_count=1)
        self.restaurant = Restaurant.objects.create(title='TestTitle', address='TestAddress')
        self.request = APIRequestFactory()
        self.request.user = self.user

    def test_raise_validation_error_when_current_day_user_vote_count_is_greater_than_user_daily_vote_count(self):
        RestaurantUserVote.objects.create(user=self.user, restaurant=self.restaurant, vote_weight=1)
        RestaurantUserVote.objects.create(user=self.user, restaurant=self.restaurant, vote_weight=1)

        with self.assertRaisesMessage(serializers.ValidationError, self.error_message):
            serializer = RestaurantUserVoteSerializer(
                data={}, context={'restaurant': self.restaurant, 'request': self.request}
            )
            serializer.is_valid(raise_exception=True)

    def test_raise_validation_error_when_current_day_user_vote_count_is_equal_to_user_daily_vote_count(self):
        RestaurantUserVote.objects.create(user=self.user, restaurant=self.restaurant, vote_weight=1)

        with self.assertRaisesMessage(serializers.ValidationError, self.error_message):
            serializer = RestaurantUserVoteSerializer(
                data={}, context={'restaurant': self.restaurant, 'request': self.request}
            )
            serializer.is_valid(raise_exception=True)

    def test_not_raise_validation_error_when_current_day_user_vote_count_is_less_than_user_daily_vote_count(self):
        serializer = RestaurantUserVoteSerializer(
            data={}, context={'restaurant': self.restaurant, 'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
