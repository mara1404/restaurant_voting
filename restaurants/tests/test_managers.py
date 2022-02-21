from datetime import datetime
from unittest import mock

from django.test import TestCase
from django.utils.timezone import make_aware

from restaurants.models import Restaurant, RestaurantUserVote
from users.models import User


class CurrentDayRestaurantUserVoteManagerShould(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u')
        self.restaurant = Restaurant.objects.create(title='TestTitle', address='TestAddress')

    @mock.patch('django.utils.timezone.now')
    def test_return_empty_queryset_when_restaurant_user_vote_created_not_current_day(self, mocked_timezone_now):
        mocked_timezone_now.return_value = make_aware(datetime(2020, 1, 1))
        RestaurantUserVote.objects.create(user=self.user, restaurant=self.restaurant, vote_weight=1)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 2, 1))

        self.assertQuerysetEqual(RestaurantUserVote.current_day_votes.all(), [])

    def test_return_queryset_with_object_when_restaurant_user_vote_created_current_day(self):
        restaurant_user_vote = RestaurantUserVote.objects.create(
            user=self.user, restaurant=self.restaurant, vote_weight=1
        )

        self.assertQuerysetEqual(RestaurantUserVote.current_day_votes.all(), [restaurant_user_vote])
