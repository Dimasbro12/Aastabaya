from os import name
from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.add_data, name='add_data'),
    path('all/', views.view_data, name="view_data"),
    path('update/<int:pk>/', views.update_data, name="update_data"),
    path('delete/<int:pk>/', views.delete_data, name="delete_data"),   
    # Page rendering views
    path('', views.apps, name='index'),
    path('signup/', views.signup_page, name='signup'),
    path('login/', views.login_page, name='login'),
    
    # API endpoints
    path('api/register/', views.register_user, name='api-register'),
    path('api/login/', views.user_login, name='api-login'),
    path('api/logout/', views.user_logout, name='api-logout'),
    path('api/sync-news/', views.sync_bps_news, name='sync-news'),
    path('api/sync-infographic/', views.sync_bps_infographic, name='sync-infographic'),
    path('api/sync-publication/', views.sync_bps_publication, name='sync-publication'),
]
