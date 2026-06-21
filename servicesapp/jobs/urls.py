from django.urls import path
from .views import (
    AdminDashboardStatsView,
    ClientJobListCreateView,
    ClientJobDetailView,
    OpenJobsListView,
    ClientDashboardStatsView,
    WorkerDashboardStatsView,
 
)

urlpatterns = [
    path("client/jobs/", ClientJobListCreateView.as_view()),
    path("client/jobs/<int:pk>/", ClientJobDetailView.as_view()),
    path("worker/open-jobs/", OpenJobsListView.as_view()),
        path('client/dashboard/stats/', ClientDashboardStatsView.as_view(), name='client-dashboard-stats'),
    path('worker/dashboard/stats/', WorkerDashboardStatsView.as_view(), name='worker-dashboard-stats'),
    path('admin/dashboard/stats/', AdminDashboardStatsView.as_view(), name='admin-dashboard-stats'),
  
]