from datetime import datetime
from unittest import mock

from django.test import TestCase
from django.utils.timezone import make_aware

from restaurants.models import Restaurant, RestaurantUserVote
from users.models import User


class RestaurantShould(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u')
        self.restaurant = Restaurant.objects.create(title='TestTitle', address='TestAddress')

    def test_return0_when_no_user_votes_exists(self):
        self.assertEqual(self.restaurant.get_user_current_day_vote_count(self.user), 0)

    @mock.patch('django.utils.timezone.now')
    def test_return_get_user_current_day_vote_count_with_votes_created_today(self, mocked_timezone_now):
        mocked_timezone_now.return_value = make_aware(datetime(2020, 1, 1))
        RestaurantUserVote.objects.create(user=self.user, restaurant=self.restaurant, vote_weight=1)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 2, 1))
        RestaurantUserVote.objects.create(user=self.user, restaurant=self.restaurant, vote_weight=1)

        self.assertEqual(self.restaurant.get_user_current_day_vote_count(self.user), 1)

    def test_return_get_user_current_day_vote_count_with_votes_created_by_given_user(self):
        user2 = User.objects.create_user(username='u2')
        RestaurantUserVote.objects.create(user=self.user, restaurant=self.restaurant, vote_weight=1)
        RestaurantUserVote.objects.create(user=user2, restaurant=self.restaurant, vote_weight=1)

        self.assertEqual(self.restaurant.get_user_current_day_vote_count(self.user), 1)

    def test_return_get_user_next_vote_weight_FIRST_VOTE_WEIGHT_when_current_day_vote_count_0(self):
        self.assertEqual(self.restaurant.get_user_next_vote_weight(self.user), self.restaurant.FIRST_VOTE_WEIGHT)

    def test_return_get_user_next_vote_weight_SECOND_VOTE_WEIGHT_when_current_day_vote_count_1(self):
        RestaurantUserVote.objects.create(user=self.user, restaurant=self.restaurant, vote_weight=1)

        self.assertEqual(self.restaurant.get_user_next_vote_weight(self.user), self.restaurant.SECOND_VOTE_WEIGHT)

    def test_return_get_user_next_vote_weight_DEFAULT_VOTE_WEIGHT_when_current_day_vote_count_greater_than_1(self):
        RestaurantUserVote.objects.create(user=self.user, restaurant=self.restaurant, vote_weight=1)
        RestaurantUserVote.objects.create(user=self.user, restaurant=self.restaurant, vote_weight=1)

        self.assertEqual(self.restaurant.get_user_next_vote_weight(self.user), self.restaurant.DEFAULT_VOTE_WEIGHT)
