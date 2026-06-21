# negotiations/urls.py
from django.urls import path
from .views import (
    GetOrCreateNegotiationView,
    SendNegotiationMessageView,
    SendProjectUpdateView,
    MarkMessagesAsReadView,
    AcceptNegotiationView,
    UserNegotiationsListView,
    AllNegotiationsListView,
    NegotiationInboxListView,  
    RejectFinalPriceView,
    SubmitFinalPriceView,
    AcceptFinalPriceView,
)

urlpatterns = [
    # Negotiation endpoints
    path('proposal/<int:proposal_id>/', GetOrCreateNegotiationView.as_view(), name='get-negotiation'),
    path('proposal/<int:proposal_id>/send/', SendNegotiationMessageView.as_view(), name='send-message'),
    path('proposal/<int:proposal_id>/send-update/', SendProjectUpdateView.as_view(), name='send-update'),
    path('proposal/<int:proposal_id>/mark-read/', MarkMessagesAsReadView.as_view(), name='mark-read'),
    path('proposal/<int:proposal_id>/accept/', AcceptNegotiationView.as_view(), name='accept-negotiation'),
    
    # List negotiations
    path('my-negotiations/', UserNegotiationsListView.as_view(), name='user-negotiations'),
    path('all-negotiations/', AllNegotiationsListView.as_view(), name='all-negotiations'),
    path('inbox/', NegotiationInboxListView.as_view(), name='negotiation-inbox'),
  
    # Final Price endpoints
    path('proposal/<int:proposal_id>/submit-final-price/', SubmitFinalPriceView.as_view(), name='submit-final-price'),
    path('proposal/<int:proposal_id>/accept-final-price/', AcceptFinalPriceView.as_view(), name='accept-final-price'),
    path('proposal/<int:proposal_id>/reject-final-price/', RejectFinalPriceView.as_view(), name='reject-final-price'),
]