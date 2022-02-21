from django.db import models
from django.utils import timezone


class CurrentDayRestaurantUserVoteManager(models.Manager):
    def get_queryset(self):
        return super(CurrentDayRestaurantUserVoteManager, self).get_queryset().filter(
            created_datetime__date=timezone.now().date()
        )
