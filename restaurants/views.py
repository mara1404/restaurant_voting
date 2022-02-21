from itertools import groupby

from django.db.models import Count, Sum, Q, Case, When
from django.db.models.functions import Coalesce
from django.utils import timezone

from rest_framework.generics import CreateAPIView, UpdateAPIView, DestroyAPIView, ListAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import RestaurantHistoryFilter, RestaurantWinnersHistoryFilter
from .models import Restaurant, RestaurantUserVote
from .serializers import RestaurantSerializer, RestaurantsListSerializer, RestaurantUserVoteSerializer, \
    RestaurantListBaseSerializer, RestaurantWinnersHistory


class CreateRestaurant(CreateAPIView):
    """View for creating restaurant"""
    permission_classes = [IsAuthenticated]
    serializer_class = RestaurantSerializer


class UpdateRestaurant(UpdateAPIView):
    """View for updating restaurant"""
    permission_classes = [IsAuthenticated]
    serializer_class = RestaurantSerializer
    queryset = Restaurant.objects.all()


class DeleteRestaurant(DestroyAPIView):
    """View for deleting restaurant"""
    permission_classes = [IsAuthenticated]
    serializer_class = RestaurantSerializer
    queryset = Restaurant.objects.all()


class ListRestaurantsBase(ListAPIView):
    """Base view for restaurant list"""
    permission_classes = [IsAuthenticated]
    queryset = Restaurant.objects.all()

    def get_restaurant_user_vote_filter(self):
        return Q()

    def annotate_unique_voted_users_and_ratings(self, queryset):
        votes_filter = self.get_restaurant_user_vote_filter()

        return queryset.annotate(
            distinct_voted_users=Count('restaurantuservote__user', distinct=True, filter=votes_filter),
            rating=Coalesce(Sum('restaurantuservote__vote_weight', filter=votes_filter), 0.0),
        ).order_by('-rating', '-distinct_voted_users', 'title')


class ListRestaurants(ListRestaurantsBase):
    """View for restaurant list. Winner restaurant is first restaurant in result list"""
    serializer_class = RestaurantsListSerializer

    def get_queryset(self):
        queryset = super(ListRestaurants, self).get_queryset().annotate(
            user_vote_count_today=Count('restaurantuservote', filter=(
                Q(restaurantuservote__created_datetime__date=timezone.now().date())
                & Q(restaurantuservote__user=self.request.user)
            )),
            can_user_vote_today=Case(
                When(user_vote_count_today__lt=self.request.user.daily_vote_count, then=True),
                default=False
            ),
        )

        return self.annotate_unique_voted_users_and_ratings(queryset)


class ListRestaurantsHistory(ListRestaurantsBase):
    """
    View for restaurant history.
    Each restaurant rating and distinct voted users counted for selected period.
    """
    serializer_class = RestaurantListBaseSerializer
    filterset_class = RestaurantHistoryFilter

    def get_restaurant_user_vote_filter(self):
        votes_filter = super(ListRestaurantsHistory, self).get_restaurant_user_vote_filter()
        date_after = self.request.query_params.get('date_after')
        date_before = self.request.query_params.get('date_before')
        if date_after:
            votes_filter = votes_filter & Q(restaurantuservote__created_datetime__gt=date_after)
        if date_before:
            votes_filter = votes_filter & Q(restaurantuservote__created_datetime__lte=date_before)

        return votes_filter

    def filter_queryset(self, queryset):
        """Annotating rating and unique voted users on filtered queryset"""
        return self.annotate_unique_voted_users_and_ratings(
            super(ListRestaurantsHistory, self).filter_queryset(queryset)
        )


class ListRestaurantWinnersHistory(ListAPIView):
    """
    View for winner restaurants.
    Returns restaurant winner for each day in given time period.
    Winner restaurant rating and distinct voted users counted separately for each day.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RestaurantWinnersHistory
    filterset_class = RestaurantWinnersHistoryFilter
    queryset = RestaurantUserVote.objects.all()

    def get_queryset(self):
        """Returns queryset with restaurant votes and distinct voted users grouped by day and restaurant"""
        return super(ListRestaurantWinnersHistory, self).get_queryset().values(
            'created_datetime__date', 'restaurant_id', 'restaurant__title', 'restaurant__address'
        ).annotate(
            rating=Sum('vote_weight'),
            total_distinct_users_voted=Count('user', distinct=True)
        ).select_related('restaurant').order_by('created_datetime__date', '-rating', '-total_distinct_users_voted')

    def list(self, request, *args, **kwargs):
        """Returns list with single winner restaurant for each day"""
        queryset = self.filter_queryset(self.get_queryset())
        # There should be a way to find winner restaurant for each day using database query, but I couldn't
        first_restaurant_of_each_day = [
            next(restaurant) for day, restaurant in groupby(queryset, key=lambda x: x['created_datetime__date'])
        ]

        page = self.paginate_queryset(first_restaurant_of_each_day)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(first_restaurant_of_each_day, many=True)

        return Response(serializer.data)


class VoteRestaurant(CreateAPIView):
    """View for voting for restaurant"""
    permission_classes = [IsAuthenticated]
    serializer_class = RestaurantUserVoteSerializer

    def get_serializer_context(self):
        context = super(VoteRestaurant, self).get_serializer_context()
        context['restaurant'] = get_object_or_404(Restaurant, pk=self.kwargs.get('pk'))

        return context

    def perform_create(self, serializer):
        restaurant = serializer.context.get('restaurant')
        serializer.save(
            restaurant=restaurant,
            vote_weight=restaurant.get_user_next_vote_weight(self.request.user),
        )
