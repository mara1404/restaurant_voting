from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimestampModelFields
from .managers import CurrentDayRestaurantUserVoteManager


class Restaurant(TimestampModelFields, models.Model):
    FIRST_VOTE_WEIGHT = 1
    SECOND_VOTE_WEIGHT = 0.5
    DEFAULT_VOTE_WEIGHT = 0.25

    title = models.CharField(max_length=255, verbose_name=_('restaurant title'))
    address = models.CharField(max_length=255, verbose_name=_('restaurant address'))

    voted_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='restaurants.RestaurantUserVote', verbose_name=_('user votes')
    )

    class Meta:
        verbose_name = _('restaurant')
        verbose_name_plural = _('restaurants')
        unique_together = ['title', 'address']

    def __str__(self):
        return self.title

    def get_user_current_day_vote_count(self, user):
        return self.restaurantuservote_set(manager='current_day_votes').filter(user=user).count()

    def get_user_next_vote_weight(self, user):
        current_day_vote_count = self.get_user_current_day_vote_count(user)

        if current_day_vote_count == 0:
            vote_weight = self.FIRST_VOTE_WEIGHT
        elif current_day_vote_count == 1:
            vote_weight = self.SECOND_VOTE_WEIGHT
        else:
            vote_weight = self.DEFAULT_VOTE_WEIGHT

        return vote_weight


class RestaurantUserVote(TimestampModelFields, models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('user'))
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, verbose_name=_('restaurant'))
    vote_weight = models.FloatField(
        validators=[MinValueValidator(0.25), MaxValueValidator(1)], verbose_name=_('vote weight')
    )

    objects = models.Manager()
    current_day_votes = CurrentDayRestaurantUserVoteManager()

    class Meta:
        verbose_name = _('restaurant user vote')
        verbose_name_plural = _('restaurant user votes')

    def __str__(self):
        return f'{self.created_datetime} - {self.user} - {self.restaurant}'
