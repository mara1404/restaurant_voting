from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import Restaurant, RestaurantUserVote


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ('title', 'address')


class RestaurantListBaseSerializer(serializers.ModelSerializer):
    distinct_voted_users = serializers.ReadOnlyField()
    rating = serializers.ReadOnlyField()

    class Meta:
        model = Restaurant
        fields = ('title', 'address', 'distinct_voted_users', 'rating')


class RestaurantWinnersHistory(serializers.ModelSerializer):
    date = serializers.ReadOnlyField(source='created_datetime__date')
    title = serializers.ReadOnlyField(source='restaurant__title')
    address = serializers.ReadOnlyField(source='restaurant__address')
    rating = serializers.ReadOnlyField()
    total_distinct_users_voted = serializers.ReadOnlyField()

    class Meta:
        model = RestaurantUserVote
        fields = ('date', 'restaurant_id', 'title', 'address', 'rating', 'total_distinct_users_voted')


class RestaurantsListSerializer(RestaurantListBaseSerializer):
    user_vote_count_today = serializers.ReadOnlyField()
    can_user_vote_today = serializers.ReadOnlyField()
    vote_url = serializers.SerializerMethodField()

    @staticmethod
    def get_vote_url(obj):
        return reverse('restaurant_vote', kwargs={'pk': obj.pk})

    class Meta:
        model = Restaurant
        fields = (
            'title', 'address', 'distinct_voted_users', 'rating', 'user_vote_count_today', 'can_user_vote_today',
            'vote_url',
        )


class RestaurantUserVoteSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = RestaurantUserVote
        fields = ['user']

    def validate(self, attrs):
        current_day_vote_count = self.context.get('restaurant').get_user_current_day_vote_count(attrs.get('user'))
        if current_day_vote_count >= attrs.get('user').daily_vote_count:
            raise serializers.ValidationError(
                _('You already voted maximum times allowed for this restaurant today'),
            )

        return attrs
