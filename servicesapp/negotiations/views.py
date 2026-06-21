# negotiations/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from .models import Negotiation, NegotiationMessage
from .serializers import NegotiationSerializer, NegotiationListSerializer, NegotiationMessageSerializer
from proposals.models import Proposal
import os
from datetime import datetime


class GetOrCreateNegotiationView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, proposal_id):
        proposal = get_object_or_404(Proposal, id=proposal_id)
        
        # Check permission
        if request.user != proposal.worker and request.user != proposal.job.client:
            return Response(
                {"error": "You don't have permission to access this negotiation"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        negotiation, created = Negotiation.objects.get_or_create(
            proposal=proposal,
            defaults={'current_offer': proposal.proposed_price}
        )
        
        serializer = NegotiationSerializer(negotiation, context={'request': request})
        return Response(serializer.data)





class SendNegotiationMessageView(generics.CreateAPIView):
    """Send negotiation messages (during negotiation phase)"""
    serializer_class = NegotiationMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})  # Important: Pass request
        return context
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        proposal_id = self.kwargs['proposal_id']
        proposal = get_object_or_404(Proposal, id=proposal_id)
        
        if self.request.user != proposal.worker and self.request.user != proposal.job.client:
            raise PermissionError("You don't have permission to send messages")
        
        negotiation, _ = Negotiation.objects.get_or_create(
            proposal=proposal,
            defaults={'current_offer': proposal.proposed_price}
        )
        
        offer = self.request.data.get('offer')
        if offer:
            try:
                negotiation.current_offer = float(offer)
                negotiation.save()
            except (ValueError, TypeError):
                pass
        
        serializer.save(
            negotiation=negotiation,
            sender=self.request.user,
            message_type='negotiation'
        )
        
        if self.request.user.role == 'client':
            negotiation.client_last_read = timezone.now()
        else:
            negotiation.worker_last_read = timezone.now()
        negotiation.save()



# negotiations/views.py - Update the SendProjectUpdateView

class SendProjectUpdateView(generics.CreateAPIView):
    """Send project updates (milestones, progress) after price is agreed"""
    serializer_class = NegotiationMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        proposal_id = self.kwargs['proposal_id']
        proposal = get_object_or_404(Proposal, id=proposal_id)
        
        # Allow both client and worker for chat messages
        if self.request.user != proposal.worker and self.request.user != proposal.job.client:
            raise PermissionError("You don't have permission to send messages")
        
        negotiation = get_object_or_404(Negotiation, proposal=proposal)
        
        # Check if price is agreed
        if not negotiation.final_price:
            raise serializers.ValidationError({"error": "Price must be agreed before sending project updates"})
        
        message_type = self.request.data.get('message_type', 'chat')
        progress = self.request.data.get('progress_percentage')
        was_completed = False  # Track if project just got completed
        
        # Validate: Only workers can send milestone/progress updates
        if message_type in ['milestone', 'progress']:
            if self.request.user != proposal.worker:
                raise PermissionError("Only the assigned worker can send progress updates")
            
            if progress is not None:
                try:
                    new_progress = int(progress)
                    current_progress = negotiation.progress_percentage or 0
                    
                    # Validate progress is between 0 and 100
                    if new_progress < 0 or new_progress > 100:
                        raise serializers.ValidationError({
                            "progress_percentage": "Progress must be between 0 and 100"
                        })
                    
                    # Validate progress can only increase, not decrease
                    if new_progress < current_progress:
                        raise serializers.ValidationError({
                            "progress_percentage": f"Progress cannot decrease. Current progress is {current_progress}%. Please enter a value greater than or equal to {current_progress}%"
                        })
                    
                    # Check if this update will complete the project
                    if new_progress == 100 and current_progress < 100:
                        was_completed = True
                    
                    # Update progress
                    negotiation.progress_percentage = new_progress
                    
                    # If progress is 100%, update project status to completed
                    if new_progress == 100:
                        negotiation.project_status = 'completed'
                        
                        # Also update the job status
                        job = proposal.job
                        job.status = 'completed'
                        job.completed_at = timezone.now()  # You'll need to add this field to JobRequest model
                        job.save()
                        
                        # Send a system message about completion
                        completion_message = NegotiationMessage.objects.create(
                            negotiation=negotiation,
                            sender=self.request.user,
                            message=f"🎉 Project marked as 100% complete! Great work on completing this project.",
                            is_system_message=True,
                            message_type='milestone'
                        )
                    
                    negotiation.save()
                    
                except (ValueError, TypeError):
                    raise serializers.ValidationError({
                        "progress_percentage": "Invalid progress value"
                    })
        
        # Create the update message
        message = serializer.save(
            negotiation=negotiation,
            sender=self.request.user,
            message_type=message_type
        )
        
        # If project was just completed, send an additional notification to client
        if was_completed:
            # You could also trigger email notifications here
            pass
        
        # Update last read
        if self.request.user.role == 'client':
            negotiation.client_last_read = timezone.now()
        else:
            negotiation.worker_last_read = timezone.now()
        negotiation.save()                
        
        
                
        
class MarkMessagesAsReadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, proposal_id):
        proposal = get_object_or_404(Proposal, id=proposal_id)
        
        # Check permission
        if request.user != proposal.worker and request.user != proposal.job.client:
            return Response(
                {"error": "You don't have permission"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        negotiation = get_object_or_404(Negotiation, proposal=proposal)
        
        # Update last read time
        if request.user.role == 'client':
            negotiation.client_last_read = timezone.now()
        else:
            negotiation.worker_last_read = timezone.now()
        negotiation.save()
        
        return Response({"success": True})


class AcceptNegotiationView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, proposal_id):
        proposal = get_object_or_404(Proposal, id=proposal_id)
        
        # Only client can accept final negotiation
        if request.user != proposal.job.client:
            return Response(
                {"error": "Only the client can accept the final negotiation"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        negotiation = get_object_or_404(Negotiation, proposal=proposal)
        
        # Set final price and close negotiation
        negotiation.final_price = negotiation.current_offer or proposal.proposed_price
        negotiation.is_active = False
        negotiation.project_status = 'in_progress'
        negotiation.save()
        
        # Update proposal
        proposal.proposed_price = negotiation.final_price
        proposal.is_selected = True
        proposal.save()
        
        # Reject other proposals
        Proposal.objects.filter(job=proposal.job).exclude(id=proposal.id).update(is_selected=False)
        
        # Update job
        job = proposal.job
        job.status = 'in_progress'
        job.worker = proposal.worker
        job.save()
        
        # Send acceptance message
        NegotiationMessage.objects.create(
            negotiation=negotiation,
            sender=request.user,
            message=f"🎉 Final price of {negotiation.final_price} accepted! The project is now in progress.",
            offer=negotiation.final_price,
            is_system_message=True,
            message_type='negotiation'
        )
        
        return Response({"success": True, "final_price": negotiation.final_price})


class UserNegotiationsListView(generics.ListAPIView):
    """Get all negotiations for the current user (both active and closed)"""
    serializer_class = NegotiationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'client':
            return Negotiation.objects.filter(
                proposal__job__client=user
            ).order_by('-updated_at')
        elif user.role == 'worker':
            return Negotiation.objects.filter(
                proposal__worker=user
            ).order_by('-updated_at')
        return Negotiation.objects.none()


class AllNegotiationsListView(generics.ListAPIView):
    serializer_class = NegotiationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'client':
            return Negotiation.objects.filter(proposal__job__client=user)
        elif user.role == 'worker':
            return Negotiation.objects.filter(proposal__worker=user)
        return Negotiation.objects.none()


class NegotiationInboxListView(generics.ListAPIView):
    """Get all negotiations for the current user with latest message preview"""
    serializer_class = NegotiationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'client':
            return Negotiation.objects.filter(
                proposal__job__client=user
            ).order_by('-updated_at')
        elif user.role == 'worker':
            return Negotiation.objects.filter(
                proposal__worker=user
            ).order_by('-updated_at')
        return Negotiation.objects.none()
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        
        current_user = request.user
        
        data = []
        for negotiation, item in zip(queryset, serializer.data):
            last_message = negotiation.messages.first()
            item['last_message'] = last_message.message[:100] if last_message else None
            item['last_message_time'] = last_message.created_at if last_message else negotiation.updated_at
            
            if current_user.role == 'client':
                item['unread_count'] = negotiation.unread_count_for_client
            else:
                item['unread_count'] = negotiation.unread_count_for_worker
            
            data.append(item)
        
        return Response(data)


class SubmitFinalPriceView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, proposal_id):
        proposal = get_object_or_404(Proposal, id=proposal_id)
        
        # Only worker can submit final price
        if request.user != proposal.worker:
            return Response(
                {"error": "Only the worker can submit a final price"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        negotiation = get_object_or_404(Negotiation, proposal=proposal)
        pending_price = request.data.get('pending_final_price')
        
        if not pending_price:
            return Response(
                {"error": "Pending final price is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pending_price = float(pending_price)
            if pending_price <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid price amount"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        negotiation.pending_final_price = pending_price
        negotiation.save()
        
        # Send a system message
        NegotiationMessage.objects.create(
            negotiation=negotiation,
            sender=request.user,
            message=f"📝 Worker has proposed a final price of KES {pending_price:,.0f}. Waiting for client approval.",
            is_system_message=True,
            message_type='negotiation'
        )
        
        return Response({
            "success": True, 
            "pending_final_price": pending_price,
            "message": "Final price submitted successfully"
        })


class AcceptFinalPriceView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, proposal_id):
        proposal = get_object_or_404(Proposal, id=proposal_id)
        
        # Only client can accept final price
        if request.user != proposal.job.client:
            return Response(
                {"error": "Only the client can accept the final price"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        negotiation = get_object_or_404(Negotiation, proposal=proposal)
        
        if not negotiation.pending_final_price:
            return Response(
                {"error": "No pending final price to accept"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set final price and update status
        negotiation.final_price = negotiation.pending_final_price
        negotiation.pending_final_price = None
        negotiation.is_active = False
        negotiation.project_status = 'in_progress'
        negotiation.save()
        
        # Update proposal
        proposal.proposed_price = negotiation.final_price
        proposal.is_selected = True
        proposal.save()
        
        # Reject other proposals
        Proposal.objects.filter(job=proposal.job).exclude(id=proposal.id).update(is_selected=False)
        
        # Update job
        job = proposal.job
        job.status = 'in_progress'
        job.worker = proposal.worker
        job.save()
        
        # Send acceptance message
        NegotiationMessage.objects.create(
            negotiation=negotiation,
            sender=request.user,
            message=f"🎉 Client has accepted the final price of KES {negotiation.final_price:,.0f}! The project is now in progress.",
            offer=negotiation.final_price,
            is_system_message=True,
            message_type='negotiation'
        )
        
        return Response({
            "success": True, 
            "final_price": negotiation.final_price,
            "project_status": negotiation.project_status,
            "message": "Price accepted successfully"
        })


class RejectFinalPriceView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, proposal_id):
        proposal = get_object_or_404(Proposal, id=proposal_id)
        
        # Only client can reject final price
        if request.user != proposal.job.client:
            return Response(
                {"error": "Only the client can reject the final price"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        negotiation = get_object_or_404(Negotiation, proposal=proposal)
        reason = request.data.get('reason', '')
        
        if not negotiation.pending_final_price:
            return Response(
                {"error": "No pending final price to reject"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Clear pending final price
        negotiation.pending_final_price = None
        negotiation.save()
        
        # Send rejection message
        message = f"Client has requested to continue negotiating."
        if reason:
            message += f" Reason: {reason}"
        
        NegotiationMessage.objects.create(
            negotiation=negotiation,
            sender=request.user,
            message=message,
            is_system_message=True,
            message_type='negotiation'
        )
        
        return Response({
            "success": True,
            "message": "Price proposal rejected"
        })