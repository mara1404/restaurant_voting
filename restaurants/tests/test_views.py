from datetime import datetime
from unittest import mock

from django.db.models import Q
from django.test import TestCase
from django.utils.timezone import make_aware

from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APIRequestFactory

from restaurants.models import Restaurant, RestaurantUserVote
from restaurants.views import ListRestaurantsBase, ListRestaurantsHistory
from users.models import User


class CreateRestaurantShould(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('restaurant_create')

    def test_return_http_403_when_user_is_anonymous(self):
        response = self.client.get(self.url)
        self.assertContains(response, status_code=403, text='')

    def test_return_http_405_when_user_is_authenticated_and_request_GET(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.get(self.url)

        self.assertContains(response, status_code=405, text='')

    def test_return_http_201_when_user_is_authenticated_and_request_POST(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.post(self.url, {'title': 'RestaurantTitle', 'address': 'test'})

        self.assertContains(response, status_code=201, text='')

    def test_create_restaurant_when_user_is_authenticated_and_request_POST(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))

        self.assertFalse(Restaurant.objects.all().exists())
        self.client.post(self.url, {'title': 'RestaurantTitle', 'address': 'test'})
        self.assertTrue(Restaurant.objects.all().exists())

    def test_create_restaurant_with_posted_fields_when_user_is_authenticated_and_request_POST(self):
        self.client.force_login(User.objects.create_user(username='u'))
        self.client.post(self.url, {'title': 'RestaurantTitle', 'address': 'test'})
        restaurant = Restaurant.objects.get()

        self.assertEqual(restaurant.title, 'RestaurantTitle')
        self.assertEqual(restaurant.address, 'test')


class UpdateRestaurantShould(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.restaurant = Restaurant.objects.create(title='TestTitle', address='TestAddress')
        self.url = self.get_url(self.restaurant.pk)

    @staticmethod
    def get_url(restaurant_id):
        return reverse('restaurant_update', kwargs={'pk': restaurant_id})

    def test_return_http_403_when_user_is_anonymous(self):
        response = self.client.get(self.url)
        self.assertContains(response, status_code=403, text='')

    def test_return_http_405_when_user_is_authenticated_and_request_GET(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.get(self.url)

        self.assertContains(response, status_code=405, text='')

    def test_return_http_200_when_user_is_authenticated_and_request_PUT(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.put(self.url, {'title': 'RestaurantTitle', 'address': 'test'})

        self.assertContains(response, status_code=200, text='')

    def test_return_http_404_when_user_is_authenticated_and_request_PUT_but_restaurant_does_not_exist(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.put(self.get_url(123123), {'title': 'RestaurantTitle', 'address': 'test'})

        self.assertContains(response, status_code=404, text='')

    def test_update_restaurant_with_posted_fields_when_user_is_authenticated_and_request_PUT(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        self.client.put(self.url, {'title': 'RestaurantTitle', 'address': 'NewAddress'})
        self.restaurant.refresh_from_db()

        self.assertEqual(self.restaurant.title, 'RestaurantTitle')
        self.assertEqual(self.restaurant.address, 'NewAddress')


class DeleteRestaurantShould(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.restaurant = Restaurant.objects.create(title='TestTitle', address='TestAddress')
        self.url = self.get_url(self.restaurant.pk)

    @staticmethod
    def get_url(restaurant_id):
        return reverse('restaurant_delete', kwargs={'pk': restaurant_id})

    def test_return_http_403_when_user_is_anonymous(self):
        response = self.client.get(self.url)
        self.assertContains(response, status_code=403, text='')

    def test_return_http_405_when_user_is_authenticated_and_request_GET(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.get(self.url)

        self.assertContains(response, status_code=405, text='')

    def test_return_http_204_when_user_is_authenticated_and_request_DELETE(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.delete(self.url)

        self.assertContains(response, status_code=204, text='')

    def test_return_http_404_when_user_is_authenticated_and_request_DELETE_but_restaurant_does_not_exist(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.delete(self.get_url(123123))

        self.assertContains(response, status_code=404, text='')

    def test_delete_restaurant_when_user_is_authenticated_and_request_DELETE(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        self.client.delete(self.url)

        self.assertFalse(Restaurant.objects.all().exists())


class ListRestaurantsBaseTestCase(TestCase):
    def test_get_restaurant_user_vote_filter_should_return_Q_object(self):
        list_restaurants_base_class = ListRestaurantsBase()
        self.assertEqual(list_restaurants_base_class.get_restaurant_user_vote_filter(), Q())


class ListRestaurantsBaseAnnotateUniqueVotedUsersAndRatingsShould(TestCase):
    def setUp(self):
        self.list_restaurants_base_class = ListRestaurantsBase()
        self.restaurant_queryset = Restaurant.objects.all()

    def test_return_empty_queryset_when_no_restaurants_exist(self):
        self.assertQuerysetEqual(
            self.list_restaurants_base_class.annotate_unique_voted_users_and_ratings(self.restaurant_queryset),
            self.restaurant_queryset
        )

    def test_annotate_distinct_voted_users_field_to_queryset(self):
        Restaurant.objects.create(title='TestTitle', address='TestAddress')
        queryset = self.list_restaurants_base_class.annotate_unique_voted_users_and_ratings(self.restaurant_queryset)

        self.assertTrue(hasattr(queryset.first(), 'distinct_voted_users'))

    def test_annotate_only_distinct_voted_users_to_queryset(self):
        user = User.objects.create_user(username='u')
        restaurant = Restaurant.objects.create(title='TestTitle', address='TestAddress')
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant, vote_weight=1)
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant, vote_weight=0.5)
        queryset = self.list_restaurants_base_class.annotate_unique_voted_users_and_ratings(self.restaurant_queryset)

        self.assertEqual(queryset.first().distinct_voted_users, 1)

    def test_annotate_rating_field_to_queryset(self):
        Restaurant.objects.create(title='TestTitle', address='TestAddress')
        queryset = self.list_restaurants_base_class.annotate_unique_voted_users_and_ratings(self.restaurant_queryset)

        self.assertTrue(hasattr(queryset.first(), 'rating'))

    def test_annotate_rating_0_when_no_users_voted(self):
        Restaurant.objects.create(title='TestTitle', address='TestAddress')
        queryset = self.list_restaurants_base_class.annotate_unique_voted_users_and_ratings(self.restaurant_queryset)

        self.assertEqual(queryset.first().rating, 0)

    def test_annotate_sum_of_user_vote_weights_when_users_voted(self):
        user1 = User.objects.create_user(username='u1')
        user2 = User.objects.create_user(username='u2')
        restaurant = Restaurant.objects.create(title='TestTitle', address='TestAddress')
        RestaurantUserVote.objects.create(user=user1, restaurant=restaurant, vote_weight=1)
        RestaurantUserVote.objects.create(user=user2, restaurant=restaurant, vote_weight=0.5)
        queryset = self.list_restaurants_base_class.annotate_unique_voted_users_and_ratings(self.restaurant_queryset)

        self.assertEqual(queryset.first().rating, 1.5)

    def test_order_queryset_by_biggest_rating(self):
        user = User.objects.create_user(username='u')
        restaurant1 = Restaurant.objects.create(title='TestTitle1', address='TestAddress')
        restaurant2 = Restaurant.objects.create(title='TestTitle2', address='TestAddress')
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant1, vote_weight=0.5)
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant2, vote_weight=1)
        queryset = self.list_restaurants_base_class.annotate_unique_voted_users_and_ratings(self.restaurant_queryset)

        self.assertQuerysetEqual(queryset, [restaurant2, restaurant1])

    def test_order_queryset_by_most_unique_users_voted_if_multiple_restaurants_with_same_rating(self):
        user1 = User.objects.create_user(username='u1')
        user2 = User.objects.create_user(username='u2')
        restaurant1 = Restaurant.objects.create(title='TestTitle1', address='TestAddress')
        restaurant2 = Restaurant.objects.create(title='TestTitle2', address='TestAddress')
        # restaurant1 votes
        RestaurantUserVote.objects.create(user=user1, restaurant=restaurant1, vote_weight=1)
        # restaurant2 votes
        RestaurantUserVote.objects.create(user=user1, restaurant=restaurant2, vote_weight=0.5)
        RestaurantUserVote.objects.create(user=user2, restaurant=restaurant2, vote_weight=0.5)
        queryset = self.list_restaurants_base_class.annotate_unique_voted_users_and_ratings(self.restaurant_queryset)

        self.assertQuerysetEqual(queryset, [restaurant2, restaurant1])

    def test_order_queryset_by_title_if_multiple_restaurants_with_same_rating_and_unique_users_count(self):
        user = User.objects.create_user(username='u')
        restaurant1 = Restaurant.objects.create(title='TestTitleB', address='TestAddress')
        restaurant2 = Restaurant.objects.create(title='TestTitleA', address='TestAddress')
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant1, vote_weight=1)
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant2, vote_weight=1)
        queryset = self.list_restaurants_base_class.annotate_unique_voted_users_and_ratings(self.restaurant_queryset)

        self.assertQuerysetEqual(queryset, [restaurant2, restaurant1])


class ListRestaurantsShould(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('restaurant_list')
        self.restaurant = Restaurant.objects.create(title='TestTitle', address='TestAddress')

    def test_return_http_403_when_user_is_anonymous(self):
        response = self.client.get(self.url)
        self.assertContains(response, status_code=403, text='')

    def test_return_http_200_when_user_is_authenticated(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.get(self.url)
        self.assertContains(response, status_code=200, text='')

    def test_have_annotated_user_vote_count_today_in_queryset(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.get(self.url)

        self.assertTrue('distinct_voted_users' in response.data.get('results')[0])

    def test_have_user_vote_count_today_0_when_no_users_voted(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.get(self.url)

        self.assertEqual(response.data.get('results')[0].get('distinct_voted_users'), 0)

    def test_have_user_vote_count_today_from_current_user(self):
        user1 = User.objects.create_user(username='u')
        user2 = User.objects.create_user(username='u2')
        self.client.force_authenticate(user1)
        RestaurantUserVote.objects.create(user=user1, restaurant=self.restaurant, vote_weight=1)
        RestaurantUserVote.objects.create(user=user2, restaurant=self.restaurant, vote_weight=1)
        RestaurantUserVote.objects.create(user=user2, restaurant=self.restaurant, vote_weight=1)
        response = self.client.get(self.url)

        self.assertEqual(response.data.get('results')[0].get('user_vote_count_today'), 1)

    @mock.patch('django.utils.timezone.now')
    def test_have_user_vote_count_today_from_current_user_current_day(self, mocked_timezone_now):
        user = User.objects.create_user(username='u')
        self.client.force_authenticate(user)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 1, 1))
        RestaurantUserVote.objects.create(user=user, restaurant=self.restaurant, vote_weight=1)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 1, 2))
        RestaurantUserVote.objects.create(user=user, restaurant=self.restaurant, vote_weight=1)
        response = self.client.get(self.url)

        self.assertEqual(response.data.get('results')[0].get('user_vote_count_today'), 1)

    def test_have_annotated_can_user_vote_today_field_in_queryset(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.get(self.url)

        self.assertTrue('can_user_vote_today' in response.data.get('results')[0])

    def test_have_can_user_vote_today_false_when_user_vote_count_today_greater_than_user_daily_vote_count(self):
        user = User.objects.create_user(username='u', daily_vote_count=1)
        self.client.force_authenticate(user)
        RestaurantUserVote.objects.create(user=user, restaurant=self.restaurant, vote_weight=1)
        RestaurantUserVote.objects.create(user=user, restaurant=self.restaurant, vote_weight=1)
        response = self.client.get(self.url)

        self.assertFalse(response.data.get('results')[0].get('can_user_vote_today'))

    def test_have_can_user_vote_today_false_when_user_vote_count_today_equal_to_user_daily_vote_count(self):
        user = User.objects.create_user(username='u', daily_vote_count=1)
        self.client.force_authenticate(user)
        RestaurantUserVote.objects.create(user=user, restaurant=self.restaurant, vote_weight=1)
        response = self.client.get(self.url)

        self.assertFalse(response.data.get('results')[0].get('can_user_vote_today'))

    def test_have_can_user_vote_today_true_when_user_vote_count_today_less_than_user_daily_vote_count(self):
        user = User.objects.create_user(username='u', daily_vote_count=2)
        self.client.force_authenticate(user)
        RestaurantUserVote.objects.create(user=user, restaurant=self.restaurant, vote_weight=1)
        response = self.client.get(self.url)

        self.assertTrue(response.data.get('results')[0].get('can_user_vote_today'))


class ListRestaurantsHistoryGetRestaurantUserVoteFilterShould(TestCase):
    def setUp(self):
        self.request = APIRequestFactory()

    def test_return_empty_Q_object_when_request_has_no_date_after_date_before_query_params(self):
        self.request.query_params = {}
        self.list_restaurants_history_class = ListRestaurantsHistory(request=self.request)
        vote_filter = self.list_restaurants_history_class.get_restaurant_user_vote_filter()

        self.assertEqual(vote_filter, Q())

    def test_return_Q_object_with_date_after_filter_when_request_has_date_after_query_param(self):
        self.request.query_params = {'date_after': datetime(2020, 1, 1).date()}
        self.list_restaurants_history_class = ListRestaurantsHistory(request=self.request)
        vote_filter = self.list_restaurants_history_class.get_restaurant_user_vote_filter()

        self.assertEqual(vote_filter, Q() & Q(restaurantuservote__created_datetime__gt=datetime(2020, 1, 1).date()))

    def test_return_Q_object_with_date_before_filter_when_request_has_date_before_query_param(self):
        self.request.query_params = {'date_before': datetime(2020, 1, 1).date()}
        self.list_restaurants_history_class = ListRestaurantsHistory(request=self.request)
        vote_filter = self.list_restaurants_history_class.get_restaurant_user_vote_filter()

        self.assertEqual(vote_filter, Q() & Q(restaurantuservote__created_datetime__lte=datetime(2020, 1, 1).date()))

    def test_return_Q_object_with_date_before_and_date_after_filters_when_request_has_both_query_params(self):
        self.request.query_params = {
            'date_after': datetime(2020, 1, 1).date(), 'date_before': datetime(2020, 2, 1).date(),
        }
        self.list_restaurants_history_class = ListRestaurantsHistory(request=self.request)
        vote_filter = self.list_restaurants_history_class.get_restaurant_user_vote_filter()

        expected_filter = (
            Q()
            & Q(restaurantuservote__created_datetime__gt=datetime(2020, 1, 1).date())
            & Q(restaurantuservote__created_datetime__lte=datetime(2020, 2, 1).date())

        )
        self.assertEqual(vote_filter, expected_filter)


class ListRestaurantsHistoryShould(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('restaurant_history')
        self.restaurant = Restaurant.objects.create(title='TestTitle', address='TestAddress')

    def test_return_http_403_when_user_is_anonymous(self):
        response = self.client.get(self.url)
        self.assertContains(response, status_code=403, text='')

    def test_return_http_200_when_user_is_authenticated(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.get(self.url)
        self.assertContains(response, status_code=200, text='')

    def test_not_filter_distinct_voted_users_when_no_before_and_no_date_after_query_params_given(self):
        user1 = User.objects.create_user(username='u')
        user2 = User.objects.create_user(username='u2')
        self.client.force_authenticate(user1)
        RestaurantUserVote.objects.create(user=user1, restaurant=self.restaurant, vote_weight=1)
        RestaurantUserVote.objects.create(user=user2, restaurant=self.restaurant, vote_weight=1)
        response = self.client.get(self.url)

        self.assertEqual(response.data.get('results')[0].get('distinct_voted_users'), 2)

    @mock.patch('django.utils.timezone.now')
    def test_filter_distinct_voted_users_when_date_before_and_date_after_query_params_given(self, mocked_timezone_now):
        user1 = User.objects.create_user(username='u1')
        user2 = User.objects.create_user(username='u2')
        self.client.force_authenticate(user1)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 1, 1))
        RestaurantUserVote.objects.create(user=user1, restaurant=self.restaurant, vote_weight=1)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 2, 1))
        RestaurantUserVote.objects.create(user=user2, restaurant=self.restaurant, vote_weight=1)
        response = self.client.get(f'{self.url}?date_after={datetime(2020, 1, 15).date()}')

        self.assertEqual(response.data.get('results')[0].get('distinct_voted_users'), 1)

    def test_not_filter_rating_when_no_before_and_no_date_after_query_params_given(self):
        user1 = User.objects.create_user(username='u1')
        user2 = User.objects.create_user(username='u2')
        self.client.force_authenticate(user1)
        RestaurantUserVote.objects.create(user=user1, restaurant=self.restaurant, vote_weight=1)
        RestaurantUserVote.objects.create(user=user2, restaurant=self.restaurant, vote_weight=0.5)
        response = self.client.get(self.url)

        self.assertEqual(response.data.get('results')[0].get('rating'), 1.5)

    @mock.patch('django.utils.timezone.now')
    def test_filter_rating_when_date_before_and_date_after_query_params_given(self, mocked_timezone_now):
        user1 = User.objects.create_user(username='u1')
        user2 = User.objects.create_user(username='u2')
        self.client.force_authenticate(user1)

        mocked_timezone_now.return_value = make_aware(datetime(2020, 1, 1))
        RestaurantUserVote.objects.create(user=user1, restaurant=self.restaurant, vote_weight=1)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 2, 1))
        RestaurantUserVote.objects.create(user=user2, restaurant=self.restaurant, vote_weight=0.5)
        response = self.client.get(f'{self.url}?date_after={datetime(2020, 1, 15).date()}')

        self.assertEqual(response.data.get('results')[0].get('rating'), 0.5)


class ListRestaurantWinnersHistoryShould(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('restaurant_winners_history')

    def test_return_http_403_when_user_is_anonymous(self):
        response = self.client.get(self.url)
        self.assertContains(response, status_code=403, text='')

    def test_return_http_200_when_user_is_authenticated(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.get(self.url)

        self.assertContains(response, status_code=200, text='')

    def test_have_empty_queryset_when_no_restaurant_user_votes_exists(self):
        user = User.objects.create_user(username='u')
        self.client.force_authenticate(user)
        response = self.client.get(self.url)

        self.assertQuerysetEqual(response.data.get('results'), [])

    @mock.patch('django.utils.timezone.now')
    def test_have_queryset_with_element_for_each_day_when_single_restaurant_votes_exists(self, mocked_timezone_now):
        user = User.objects.create_user(username='u')
        self.client.force_authenticate(user)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 1, 1))
        restaurant = Restaurant.objects.create(title='TestTitle', address='TestAddress')
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant, vote_weight=0.5)
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant, vote_weight=0.5)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 1, 3))
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant, vote_weight=0.5)
        response = self.client.get(self.url)

        self.assertListEqual(
            [result['date'] for result in response.data.get('results')],
            [datetime(2020, 1, 1).date(), datetime(2020, 1, 3).date()]
        )

    @mock.patch('django.utils.timezone.now')
    def test_have_queryset_with_each_day_rating_sum_when_single_restaurant_votes_exists(self, mocked_timezone_now):
        user = User.objects.create_user(username='u')
        user2 = User.objects.create_user(username='u2')
        self.client.force_authenticate(user)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 1, 1))
        restaurant = Restaurant.objects.create(title='TestTitle', address='TestAddress')
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant, vote_weight=1)
        RestaurantUserVote.objects.create(user=user2, restaurant=restaurant, vote_weight=0.7)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 1, 3))
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant, vote_weight=0.8)
        response = self.client.get(self.url)

        self.assertListEqual(
            [(result['date'], result['rating']) for result in response.data.get('results')],
            [(datetime(2020, 1, 1).date(), 1.7), (datetime(2020, 1, 3).date(), 0.8)]
        )

    @mock.patch('django.utils.timezone.now')
    def test_have_queryset_with_each_day_total_distinct_users_voted_when_single_restaurant_votes_exists(
            self, mocked_timezone_now
    ):
        user = User.objects.create_user(username='u')
        user2 = User.objects.create_user(username='u2')
        self.client.force_authenticate(user)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 1, 1))
        restaurant = Restaurant.objects.create(title='TestTitle', address='TestAddress')
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant, vote_weight=1)
        RestaurantUserVote.objects.create(user=user2, restaurant=restaurant, vote_weight=0.7)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 1, 3))
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant, vote_weight=0.8)
        response = self.client.get(self.url)

        self.assertListEqual(
            [(result['date'], result['total_distinct_users_voted']) for result in response.data.get('results')],
            [(datetime(2020, 1, 1).date(), 2), (datetime(2020, 1, 3).date(), 1)]
        )

    @mock.patch('django.utils.timezone.now')
    def test_have_queryset_with_each_day_biggest_rating_when_multiple_restaurant_votes_exists(
            self, mocked_timezone_now
    ):
        user = User.objects.create_user(username='u')
        user2 = User.objects.create_user(username='u2')
        self.client.force_authenticate(user)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 1, 1))
        restaurant1 = Restaurant.objects.create(title='TestTitle1', address='TestAddress')
        restaurant2 = Restaurant.objects.create(title='TestTitle2', address='TestAddress')
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant1, vote_weight=1)
        RestaurantUserVote.objects.create(user=user2, restaurant=restaurant1, vote_weight=0.7)
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant2, vote_weight=1)
        RestaurantUserVote.objects.create(user=user2, restaurant=restaurant2, vote_weight=0.9)
        response = self.client.get(self.url)

        self.assertListEqual(
            [(result['date'], result['rating']) for result in response.data.get('results')],
            [(datetime(2020, 1, 1).date(), 1.9)]
        )

    @mock.patch('django.utils.timezone.now')
    def test_have_queryset_with_each_day_biggest_total_distinct_users_voted_when_restaurants_have_same_rating(
            self, mocked_timezone_now
    ):
        user = User.objects.create_user(username='u')
        user2 = User.objects.create_user(username='u2')
        self.client.force_authenticate(user)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 1, 1))
        restaurant1 = Restaurant.objects.create(title='TestTitle1', address='TestAddress')
        restaurant2 = Restaurant.objects.create(title='TestTitle2', address='TestAddress')
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant1, vote_weight=1)
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant1, vote_weight=1)
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant2, vote_weight=1)
        RestaurantUserVote.objects.create(user=user2, restaurant=restaurant2, vote_weight=1)
        response = self.client.get(self.url)

        self.assertListEqual(
            [(result['date'], result['total_distinct_users_voted']) for result in response.data.get('results')],
            [(datetime(2020, 1, 1).date(), 2)]
        )

    @mock.patch('django.utils.timezone.now')
    def test_have_queryset_with_first_same_day_restaurant_when_total_rating_and_distinct_user_votes_are_same(
            self, mocked_timezone_now
    ):
        user = User.objects.create_user(username='u')
        user2 = User.objects.create_user(username='u2')
        self.client.force_authenticate(user)
        mocked_timezone_now.return_value = make_aware(datetime(2020, 1, 1))
        restaurant1 = Restaurant.objects.create(title='TestTitle1', address='TestAddress')
        restaurant2 = Restaurant.objects.create(title='TestTitle2', address='TestAddress')
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant1, vote_weight=0.3)
        RestaurantUserVote.objects.create(user=user2, restaurant=restaurant1, vote_weight=0.3)
        RestaurantUserVote.objects.create(user=user, restaurant=restaurant2, vote_weight=0.3)
        RestaurantUserVote.objects.create(user=user2, restaurant=restaurant2, vote_weight=0.3)
        response = self.client.get(self.url)

        result_list = [
            (result['date'], result['restaurant_id'], result['rating'], result['total_distinct_users_voted'])
            for result in response.data.get('results')
        ]
        self.assertListEqual(result_list, [(datetime(2020, 1, 1).date(), restaurant1.pk, 0.6, 2)])


class VoteRestaurantShould(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.restaurant = Restaurant.objects.create(title='TestTitle', address='TestAddress')
        self.url = self.get_url(self.restaurant.pk)

    @staticmethod
    def get_url(restaurant_id):
        return reverse('restaurant_vote', kwargs={'pk': restaurant_id})

    def test_return_http_403_when_user_is_anonymous(self):
        response = self.client.get(self.url)
        self.assertContains(response, status_code=403, text='')

    def test_return_http_405_when_user_is_authenticated_and_request_GET(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.get(self.url)

        self.assertContains(response, status_code=405, text='')

    def test_return_http_201_when_user_is_authenticated_and_request_POST(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.post(self.url, {})

        self.assertContains(response, status_code=201, text='')

    def test_return_http_404_when_user_is_authenticated_and_request_POST_but_restaurant_does_not_exist(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))
        response = self.client.post(self.get_url(123123), {})

        self.assertContains(response, status_code=404, text='')

    def test_create_restaurant_user_vote_when_user_is_authenticated_and_request_POST(self):
        self.client.force_authenticate(User.objects.create_user(username='u'))

        self.assertFalse(RestaurantUserVote.objects.all().exists())
        self.client.post(self.url, {})
        self.assertTrue(RestaurantUserVote.objects.all().exists())

    def test_create_restaurant_user_vote_with_user_and_restaurant_when_user_is_authenticated_and_request_POST(self):
        user = User.objects.create_user(username='u')
        self.client.force_login(user)
        self.client.post(self.url, {})
        restaurant_user_vote = RestaurantUserVote.objects.get()

        self.assertEqual(restaurant_user_vote.user, user)
        self.assertEqual(restaurant_user_vote.restaurant, self.restaurant)
