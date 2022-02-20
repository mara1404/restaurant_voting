from django.db.models import Count, Sum, Q, Case, When
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.generics import CreateAPIView, UpdateAPIView, DestroyAPIView, ListAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated

from .filters import RestaurantHistoryFilter
from .models import Restaurant
from .serializers import RestaurantSerializer, RestaurantsListSerializer, RestaurantUserVoteSerializer, \
    RestaurantListBaseSerializer


class CreateRestaurant(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RestaurantSerializer


class UpdateRestaurant(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RestaurantSerializer
    queryset = Restaurant.objects.all()


class DeleteRestaurant(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RestaurantSerializer
    queryset = Restaurant.objects.all()


class ListRestaurantsBase(ListAPIView):
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
        return self.annotate_unique_voted_users_and_ratings(
            super(ListRestaurantsHistory, self).filter_queryset(queryset)
        )


class VoteRestaurant(CreateAPIView):
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
