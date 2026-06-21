# reviews/views.py - Simplified version

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Review, UserRating
from .serializers import ReviewSerializer, CreateReviewSerializer, UserRatingSerializer
from jobs.models import JobRequest


class CreateReviewView(generics.CreateAPIView):
    """Create a review for a completed project"""
    serializer_class = CreateReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Manually create the review with reviewer from request.user
        review_data = serializer.validated_data
        review = Review.objects.create(
            job=review_data['job'],
            reviewer=request.user,
            reviewee=review_data['reviewee'],
            review_type=review_data['review_type'],
            rating=review_data['rating'],
            comment=review_data['comment'],
            communication_rating=review_data.get('communication_rating'),
            quality_rating=review_data.get('quality_rating'),
            punctuality_rating=review_data.get('punctuality_rating'),
        )
        
        # Update user rating summary for the reviewee
        user_rating, _ = UserRating.objects.get_or_create(user=review.reviewee)
        user_rating.update_ratings()
        
        # Return simple success response
        return Response({
            'success': True,
            'message': 'Review submitted successfully',
            'review_id': review.id,
            'rating': review.rating
        }, status=status.HTTP_201_CREATED)


class CheckReviewStatusView(generics.GenericAPIView):
    """Check if user can review a project"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, job_id):
        job = get_object_or_404(JobRequest, id=job_id)
        
        is_completed = job.status == 'completed'
        
        # Check if client can review worker
        client_can_review = (
            is_completed and 
            request.user == job.client and 
            job.worker and
            not Review.objects.filter(job=job, reviewer=request.user, review_type='client_to_worker').exists()
        )
        
        # Check if worker can review client
        worker_can_review = (
            is_completed and 
            request.user == job.worker and 
            not Review.objects.filter(job=job, reviewer=request.user, review_type='worker_to_client').exists()
        )
        
        # Get existing reviews
        client_review = Review.objects.filter(job=job, review_type='client_to_worker').first()
        worker_review = Review.objects.filter(job=job, review_type='worker_to_client').first()
        
        return Response({
            'is_completed': is_completed,
            'client_can_review': client_can_review,
            'worker_can_review': worker_can_review,
            'client_review_exists': bool(client_review),
            'worker_review_exists': bool(worker_review),
            'job': {
                'id': job.id,
                'title': job.title,
                'client_name': job.client.full_name,
                'worker_name': job.worker.full_name if job.worker else None,
            }
        })


class JobReviewsView(generics.ListAPIView):
    """Get all reviews for a specific job"""
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        job_id = self.kwargs['job_id']
        return Review.objects.filter(job_id=job_id, is_public=True)


class UserReviewsView(generics.ListAPIView):
    """Get all reviews for a specific user"""
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id', self.request.user.id)
        return Review.objects.filter(reviewee_id=user_id, is_public=True)


class UserRatingView(generics.RetrieveAPIView):
    """Get rating summary for a user"""
    serializer_class = UserRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        user_id = self.kwargs.get('user_id', self.request.user.id)
        obj, created = UserRating.objects.get_or_create(user_id=user_id)
        return obj


class MyReviewsView(generics.ListAPIView):
    """Get reviews given by the current user"""
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Review.objects.filter(reviewer=self.request.user)


class DeleteReviewView(generics.DestroyAPIView):
    """Delete a review (admin only)"""
    queryset = Review.objects.all()
    permission_classes = [permissions.IsAdminUser]