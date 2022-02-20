from django.urls import path, include

from . import views

urlpatterns = [
    path('create/', views.CreateRestaurant.as_view(), name='restaurant_create'),
    path('list/', views.ListRestaurants.as_view(), name='restaurant_list'),
    path('history/', views.ListRestaurantsHistory.as_view(), name='restaurant_history'),
    path('<int:pk>/', include([
        path('update/', views.UpdateRestaurant.as_view(), name='restaurant_update'),
        path('delete/', views.DeleteRestaurant.as_view(), name='restaurant_delete'),
        path('vote/', views.VoteRestaurant.as_view(), name='restaurant_vote'),
    ])),
]
