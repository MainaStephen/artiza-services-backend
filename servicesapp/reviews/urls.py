from django.urls import path
from .views import (
    CreateReviewView,
    CheckReviewStatusView,
    JobReviewsView,
    UserReviewsView,
    UserRatingView,
    MyReviewsView,
    DeleteReviewView,
)

urlpatterns = [
    path('create/', CreateReviewView.as_view(), name='create-review'),
    path('check/<int:job_id>/', CheckReviewStatusView.as_view(), name='check-review'),
    path('job/<int:job_id>/', JobReviewsView.as_view(), name='job-reviews'),
    path('user/<int:user_id>/', UserReviewsView.as_view(), name='user-reviews'),
    path('user/rating/<int:user_id>/', UserRatingView.as_view(), name='user-rating'),
    path('my-reviews/', MyReviewsView.as_view(), name='my-reviews'),
    path('<int:pk>/delete/', DeleteReviewView.as_view(), name='delete-review'),
]