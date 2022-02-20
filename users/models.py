from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    daily_vote_count = models.PositiveSmallIntegerField(default=4, verbose_name=_('daily vote count'))
