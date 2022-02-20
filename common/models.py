from django.db import models
from django.utils.translation import gettext_lazy as _


class TimestampModelFields(models.Model):
    created_datetime = models.DateTimeField(auto_now_add=True, verbose_name=_('creation date'))
    updated_datetime = models.DateTimeField(auto_now=True, verbose_name=_('last update date'))

    class Meta:
        abstract = True
