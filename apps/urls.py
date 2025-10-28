from os import name
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ApiOverview, name='home'),
    path('apps/', views.apps, name='apps'),
    path('register/', views.register_user, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('create/', views.add_data, name='add_data'),
    path('all/', views.view_data, name="view_data"),
    path('update/<int:pk>/', views.update_data, name="update_data"),
    path('delete/<int:pk>/', views.delete_data, name="delete_data"),   
]
