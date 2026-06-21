from django.urls import path
from .views import ArtisanApplicationCreateView, AdminArtisanApplicationsView, ArtisanApplicationStatusUpdateView


urlpatterns = [
    path('apply-to-be-a-worker/', ArtisanApplicationCreateView.as_view(), name='artisan-application-post'),
    path('admin/applications/', AdminArtisanApplicationsView.as_view(), name='admin-artisan-applications'),
    path("admin/applications/<int:pk>/update-status/", ArtisanApplicationStatusUpdateView.as_view(), name="artisan-application-update-status"),
    
]
