# portfolio/urls.py
from django.urls import path
from .views import (
    GetOrCreatePortfolioView,
    UpdatePortfolioView,
    PublicPortfolioView,
    AddPortfolioImageView,
    DeletePortfolioImageView,
    WorkerCompletedProjectsView,
)

urlpatterns = [
    path('my-portfolio/', GetOrCreatePortfolioView.as_view(), name='my-portfolio'),
    path('my-portfolio/update/', UpdatePortfolioView.as_view(), name='update-portfolio'),
    path('my-portfolio/add-image/', AddPortfolioImageView.as_view(), name='add-portfolio-image'),
    path('my-portfolio/delete-image/<int:pk>/', DeletePortfolioImageView.as_view(), name='delete-portfolio-image'),
    path('public/<int:worker_id>/', PublicPortfolioView.as_view(), name='public-portfolio'),
    path('worker/<int:worker_id>/completed-projects/', WorkerCompletedProjectsView.as_view(), name='worker-completed-projects'),
]