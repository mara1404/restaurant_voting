from django.contrib import admin

from .models import Restaurant, RestaurantUserVote


class RestaurantUserVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'restaurant', 'vote_weight', 'created_datetime']

    def get_queryset(self, request):
        return super(RestaurantUserVoteAdmin, self).get_queryset(request).select_related('user', 'restaurant')


admin.site.register(RestaurantUserVote, RestaurantUserVoteAdmin)
admin.site.register(Restaurant)
