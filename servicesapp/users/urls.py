# from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView
# from .views import (
#     CustomLoginView,
#     RegisterUserView,
#     CreateWorkerView,
#     ActivateWorkerView,
#     # RegisterClientView,
#     PendingWorkerApplicationsView,
#     ResendActivationEmailView,
#     UserProfileView,
#     ChangePasswordView,
#     ClientStatsView,
#     WorkerStatsView,
    
# )

# urlpatterns = [
  
#     path("login/", CustomLoginView.as_view(), name="login"),
#     path("register/", RegisterUserView.as_view(), name="register"),
#     # Admin: Create worker
#     path('admin/create-worker/', CreateWorkerView.as_view(), name='create-worker'),
    
#     # Worker activation
#     path('activate-worker/<str:uidb64>/<str:token>/', ActivateWorkerView.as_view(), name='activate-worker'),
    
#     # Admin: View pending applications
#     path('admin/pending-applications/', PendingWorkerApplicationsView.as_view(), name='pending-applications'),
    
#     # Admin: Resend activation email
#     path('admin/resend-activation/<int:user_id>/', ResendActivationEmailView.as_view(), name='resend-activation'),
#         path('profile/', UserProfileView.as_view(), name='user-profile'),
#     path('change-password/', ChangePasswordView.as_view(), name='change-password'),
#     path('client/stats/', ClientStatsView.as_view(), name='client-stats'),
#     path('worker/stats/', WorkerStatsView.as_view(), name='worker-stats'),

# ]


# users/urls.py - Add admin user management URLs

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomLoginView,
    RegisterUserView,
    CreateWorkerView,
    ActivateWorkerView,
    PendingWorkerApplicationsView,
    ResendActivationEmailView,
    UserProfileView,
    ChangePasswordView,
    ClientStatsView,
    WorkerStatsView,
    AdminAllUsersView,
    AdminUserDetailView,
    AdminCreateWorkerView,
    AdminToggleUserStatusView,
    AdminMakeAdminView,
)

urlpatterns = [
    # Authentication URLs
    path("login/", CustomLoginView.as_view(), name="login"),
    path("register/", RegisterUserView.as_view(), name="register"),
    
    # Profile URLs
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Stats URLs
    path('client/stats/', ClientStatsView.as_view(), name='client-stats'),
    path('worker/stats/', WorkerStatsView.as_view(), name='worker-stats'),
    
    # Worker Management URLs
    path('admin/create-worker/', CreateWorkerView.as_view(), name='create-worker'),
    path('activate-worker/<str:uidb64>/<str:token>/', ActivateWorkerView.as_view(), name='activate-worker'),
    path('admin/pending-applications/', PendingWorkerApplicationsView.as_view(), name='pending-applications'),
    path('admin/resend-activation/<int:user_id>/', ResendActivationEmailView.as_view(), name='resend-activation'),
    
    # Admin User Management URLs
    path('admin/users/', AdminAllUsersView.as_view(), name='admin-users'),
    path('admin/users/<int:user_id>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/create-worker/', AdminCreateWorkerView.as_view(), name='admin-create-worker'),
    path('admin/users/toggle-status/<int:user_id>/', AdminToggleUserStatusView.as_view(), name='admin-toggle-status'),
    path('admin/users/make-admin/<int:user_id>/', AdminMakeAdminView.as_view(), name='admin-make-admin'),
    
]