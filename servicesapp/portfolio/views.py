# portfolio/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import models
from django.utils import timezone
from .models import WorkerPortfolio, PortfolioImage
from .serializers import WorkerPortfolioSerializer, WorkerPortfolioUpdateSerializer, PortfolioImageSerializer
from jobs.models import JobRequest
from users.models import User
from reviews.models import Review


class GetOrCreatePortfolioView(APIView):
    """Get or create portfolio for the authenticated worker"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if user.role != 'worker':
            return Response(
                {"error": "Only workers can have portfolios"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        portfolio, created = WorkerPortfolio.objects.get_or_create(worker=user)
        serializer = WorkerPortfolioSerializer(portfolio, context={'request': request})
        
        return Response(serializer.data)


class UpdatePortfolioView(generics.UpdateAPIView):
    """Update worker portfolio"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WorkerPortfolioUpdateSerializer
    
    def get_object(self):
        return get_object_or_404(WorkerPortfolio, worker=self.request.user)


class PublicPortfolioView(APIView):
    """View public portfolio of any worker"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, worker_id):
        portfolio = get_object_or_404(WorkerPortfolio, worker_id=worker_id, is_active=True)
        serializer = WorkerPortfolioSerializer(portfolio, context={'request': request})
        return Response(serializer.data)


class AddPortfolioImageView(generics.CreateAPIView):
    """Add extra image to portfolio"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PortfolioImageSerializer
    
    def perform_create(self, serializer):
        portfolio = get_object_or_404(WorkerPortfolio, worker=self.request.user)
        serializer.save(portfolio=portfolio)


class DeletePortfolioImageView(APIView):
    """Remove image from portfolio"""
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, pk):
        image = get_object_or_404(PortfolioImage, pk=pk, portfolio__worker=request.user)
        image.delete()
        return Response({"message": "Image deleted successfully"}, status=status.HTTP_200_OK)


class WorkerCompletedProjectsView(APIView):
    """Get all completed projects for a worker"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, worker_id):
        worker = get_object_or_404(User, id=worker_id, role='worker')
        
        # Use created_at as completion date since completed_at doesn't exist
        completed_jobs = JobRequest.objects.filter(
            worker=worker,
            status='completed'
        ).select_related('client').order_by('-updated_at', '-created_at')
        
        data = []
        for job in completed_jobs:
            review = Review.objects.filter(job=job, review_type='client_to_worker').first()
            
            # Get images
            images = []
            for img in job.images.all():
                if request:
                    images.append(request.build_absolute_uri(img.image.url))
                else:
                    images.append(img.image.url)
            
            # Get final price from negotiation if available
            final_price = None
            accepted_proposal = job.proposals.filter(is_selected=True).first()
            if accepted_proposal and hasattr(accepted_proposal, 'negotiation'):
                final_price = accepted_proposal.negotiation.final_price
            
            data.append({
                'id': job.id,
                'title': job.title,
                'description': job.description,
                'category': job.category,
                'budget': float(job.budget) if job.budget else None,
                'final_price': float(final_price) if final_price else float(job.budget) if job.budget else None,
                'location': job.location,
                'completed_at': job.updated_at.strftime('%Y-%m-%d') if job.status == 'completed' else job.created_at.strftime('%Y-%m-%d'),
                'client_name': job.client.full_name,
                'client_avatar': f"https://ui-avatars.com/api/?name={job.client.full_name}&background=2c7da0&color=fff",
                'images': images,
                'review': {
                    'rating': review.rating if review else None,
                    'comment': review.comment[:200] if review and review.comment else None,
                } if review else None
            })
        
        return Response({
            'count': len(data),
            'projects': data
        })