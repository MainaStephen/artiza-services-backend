from django.urls import path
from .views import (
    ProposalCreateView,
    WorkerProposalsListView,
    ClientJobProposalsListView,
    SelectProposalView
)

urlpatterns = [
    path("post-proposals/<int:job_id>/", ProposalCreateView.as_view(), name="create-proposal"),
    path("get-worker-proposals/", WorkerProposalsListView.as_view(), name="list-worker-proposals"),
    path("job/<int:job_id>/proposals/", ClientJobProposalsListView.as_view(), name="job-proposals"),
    path("<int:proposal_id>/select/", SelectProposalView.as_view(), name="select-proposal"),
]