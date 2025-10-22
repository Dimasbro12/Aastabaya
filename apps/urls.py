from django.urls import path
from . import views

urlpatterns = [
    path('apps/', views.apps, name='apps'),
]
