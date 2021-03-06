# Generated by Django 3.2.12 on 2022-02-16 14:39

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Restaurant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name='creation date')),
                ('updated_datetime', models.DateTimeField(auto_now=True, verbose_name='last update date')),
                ('title', models.CharField(max_length=255, verbose_name='restaurant title')),
                ('address', models.CharField(max_length=255, verbose_name='restaurant address')),
            ],
            options={
                'verbose_name': 'restaurant',
                'verbose_name_plural': 'restaurants',
            },
        ),
        migrations.CreateModel(
            name='RestaurantUserVote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name='creation date')),
                ('updated_datetime', models.DateTimeField(auto_now=True, verbose_name='last update date')),
                ('vote_weight', models.FloatField(validators=[django.core.validators.MinValueValidator(0.25), django.core.validators.MaxValueValidator(1)], verbose_name='vote weight')),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='restaurants.restaurant', verbose_name='restaurant')),
            ],
            options={
                'verbose_name': 'restaurant user vote',
                'verbose_name_plural': 'restaurant user votes',
            },
        ),
    ]
