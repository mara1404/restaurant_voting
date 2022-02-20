# Generated by Django 3.2.12 on 2022-02-16 14:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('restaurants', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurantuservote',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='user'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='voted_users',
            field=models.ManyToManyField(through='restaurants.RestaurantUserVote', to=settings.AUTH_USER_MODEL, verbose_name='user votes'),
        ),
        migrations.AlterUniqueTogether(
            name='restaurant',
            unique_together={('title', 'address')},
        ),
    ]