from django.urls import path
from . import views
# from rest_framework.routers import DefaultRouter
from apps.views import NewsViewSet, InpographicViewSet, PublicationViewSet,HumanDevelopmentIndexViewSet 
# from . import consumers
# router = DefaultRouter()
# router.register(r'news', NewsViewSet, basename='news')
# router.register(r'infographics', InpographicViewSet, basename='infographic')
# router.register(r'publications', PublicationViewSet, basename='publication')
# router.register(r'human-development-index', HumanDevelopmentIndexViewSet, basename='human-development-index')

# websocket_urlpatterns = [
#     path("ws/chat/", consumers.ChatConsumer.as_asgi()),
# ]
urlpatterns = [
    
    # path('api/v1/', (router.urls)),
    # Page rendering views
    path('', views.apps, name='index'),
    path('signup/', views.signup_page, name='signup'),
    path('login/', views.login_page, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('infographics/', views.infographics, name='infographics'),
    path('publications/', views.publications, name='publications'),
    path('news/', views.news, name='news'),
    path('ipm/', views.ipm, name='ipm'),
    
    # URL for contact form submission
    path('contact-us/', views.contact_us, name='contact_us'),

    # API endpoints for authentication
    path('api/register/', views.register_user, name='api-register'),
    path('api/login/', views.user_login, name='api-login'),
    path('api/logout/', views.user_logout, name='api-logout'),

    # API endpoints for BPS data synchronization
    path('api/sync/news/', views.sync_bps_news, name='sync-bps-news'),
    path('api/sync/infographics/', views.sync_bps_infographic, name='sync-bps-infographics'),
    path('api/sync/publications/', views.sync_bps_publication, name='sync-bps-publications'),
    
    # API endpoints for Spreadsheet data synchronization
    path('api/sync/human-development-index/', views.sync_human_development_index, name='sync-human-development-index'),
    # path('api/sync/hotel-occupancy-combined/', views.sync_hotel_occupancy_combined, name='sync-hotel-occupancy-combined'),
    # path('api/sync/hotel-occupancy-yearly/', views.sync_hotel_occupancy_yearly, name='sync-hotel-occupancy-yearly'),
    
    # API endpoints for generic data
    path('api/data/', views.view_data, name='view-data'),
    path('api/data/add/', views.add_data, name='add-data'),
    path('api/data/update/<int:pk>/', views.update_data, name='update-data'),
    path('api/data/delete/<int:pk>/', views.delete_data, name='delete-data'),
] 
