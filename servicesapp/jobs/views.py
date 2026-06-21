from rest_framework import generics, permissions
from .models import JobRequest
from .serializer import JobRequestSerializer, JobRequestCreateSerializer
from .utils import is_within_radius

class ClientJobListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return JobRequestCreateSerializer
        return JobRequestSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role != "client":
            return JobRequest.objects.none()

        return JobRequest.objects.filter(client=user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)
        
        

class ClientJobDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role != "client":
            return JobRequest.objects.none()

        return JobRequest.objects.filter(client=user)
    





class OpenJobsListView(generics.ListAPIView):
    serializer_class = JobRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # 1. Only workers
        if user.role != "worker":
            return JobRequest.objects.none()

        # 2. Must have skill
        if not user.skill:
            return JobRequest.objects.none()

        # 3. Must have location
        if user.latitude is None or user.longitude is None:
            return JobRequest.objects.none()

        worker_lat = user.latitude
        worker_lng = user.longitude

        # 4. Pre-filter DB (IMPORTANT OPTIMIZATION)
        jobs = JobRequest.objects.filter(
            status="pending",
            category=user.skill,
            latitude__isnull=False,
            longitude__isnull=False
        ).order_by("-created_at")

        nearby_job_ids = []

        for job in jobs:
            if is_within_radius(
                job.latitude,
                job.longitude,
                worker_lat,
                worker_lng,
                radius_km=20
            ):
                nearby_job_ids.append(job.id)

        return JobRequest.objects.filter(id__in=nearby_job_ids)
    
    
    
    
    
    
    
# jobs/views.py - Add these dashboard views

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta
from .models import JobRequest, JobImage
from proposals.models import Proposal
from negotiations.models import Negotiation, NegotiationMessage
from reviews.models import Review


class ClientDashboardStatsView(APIView):
    """Get client dashboard statistics and data"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if user.role != 'client':
            return Response(
                {"error": "This endpoint is for clients only"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get client's jobs
        jobs = JobRequest.objects.filter(client=user)
        
        # Calculate stats
        active_projects = jobs.filter(status__in=['accepted', 'in_progress']).count()
        pending_proposals = Proposal.objects.filter(
            job__client=user,
            is_selected=False
        ).exclude(
            job__status__in=['completed', 'cancelled']
        ).count()
        ongoing_jobs = jobs.filter(status='in_progress').count()
        completed_jobs = jobs.filter(status='completed').count()
        
        # Calculate total spent from accepted proposals
        accepted_proposals = Proposal.objects.filter(
            job__client=user,
            is_selected=True
        )
        total_spent = sum(p.proposed_price for p in accepted_proposals if p.proposed_price)
        
        # Get recent proposals
        recent_proposals = Proposal.objects.filter(
            job__client=user,
            is_selected=False
        ).select_related('worker', 'job').order_by('-created_at')[:5]
        
        recent_proposals_data = []
        for proposal in recent_proposals:
            recent_proposals_data.append({
                'id': proposal.id,
                'project_id': proposal.job.id,
                'project': proposal.job.title,
                'artisan': proposal.worker.full_name,
                'rating': self.get_worker_rating(proposal.worker),
                'amount': f"KES {int(proposal.proposed_price):,}",
                'submitted': self.get_time_ago(proposal.created_at),
                'avatar': f"https://ui-avatars.com/api/?name={proposal.worker.full_name}&background=2c7da0&color=fff"
            })
        
        # Get recent messages from negotiations
        negotiations = Negotiation.objects.filter(
            proposal__job__client=user
        ).order_by('-updated_at')[:5]
        
        recent_messages = []
        for negotiation in negotiations:
            last_message = negotiation.messages.first()
            if last_message:
                recent_messages.append({
                    'id': negotiation.id,
                    'project_id': negotiation.proposal.job.id,
                    'from': last_message.sender.full_name,
                    'message': last_message.message[:100],
                    'time': self.get_time_ago(last_message.created_at),
                    'read': False,  # You can implement read tracking
                    'type': self.get_message_type(last_message.message_type)
                })
        
        # Get active projects preview
        active_projects_list = jobs.filter(
            status__in=['pending', 'accepted', 'in_progress']
        ).order_by('-created_at')[:3]
        
        active_projects_data = []
        for job in active_projects_list:
            proposals_count = Proposal.objects.filter(job=job).count()
            negotiation = None
            progress = 0
            
            # Get progress if job is in progress
            if job.status == 'in_progress':
                accepted_proposal = job.proposals.filter(is_selected=True).first()
                if accepted_proposal and hasattr(accepted_proposal, 'negotiation'):
                    progress = accepted_proposal.negotiation.progress_percentage or 0
            
            active_projects_data.append({
                'id': job.id,
                'title': job.title,
                'category': job.category,
                'status': 'open' if job.status == 'pending' else 'in_progress',
                'proposals': proposals_count,
                'posted_date': self.get_time_ago(job.created_at),
                'budget': f"KES {int(job.budget):,}" if job.budget else 'N/A',
                'progress': progress
            })
        
        return Response({
            'stats': {
                'active_projects': active_projects,
                'completed_jobs': completed_jobs,
                'pending_proposals': pending_proposals,
                'ongoing_jobs': ongoing_jobs,
                'total_spent': f"KES {int(total_spent):,}"
            },
            'recent_proposals': recent_proposals_data,
            'recent_messages': recent_messages,
            'active_projects': active_projects_data
        })
    
    def get_worker_rating(self, worker):
        """Get worker's average rating"""
        reviews = Review.objects.filter(reviewee=worker)
        avg = reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0
    
    def get_time_ago(self, date):
        """Convert datetime to time ago string"""
        now = timezone.now()
        diff = now - date
        
        if diff.days > 7:
            return date.strftime('%b %d, %Y')
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
    def get_message_type(self, message_type):
        """Map message type to icon type"""
        if message_type == 'negotiation':
            return 'negotiation'
        elif message_type == 'milestone':
            return 'update'
        else:
            return 'proposal'


class WorkerDashboardStatsView(APIView):
    """Get worker dashboard statistics and data"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if user.role != 'worker':
            return Response(
                {"error": "This endpoint is for workers only"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get worker's proposals
        proposals = Proposal.objects.filter(worker=user)
        
        # Calculate stats
        open_projects = JobRequest.objects.filter(
            status='pending'
        ).count()
        
        proposals_submitted = proposals.count()
        ongoing_projects = proposals.filter(
            is_selected=True,
            job__status__in=['accepted', 'in_progress']
        ).count()
        completed_projects = proposals.filter(job__status='completed').count()
        
        # Calculate total earnings
        completed_proposals = proposals.filter(job__status='completed', is_selected=True)
        total_earnings = sum(p.proposed_price for p in completed_proposals if p.proposed_price)
        
        # Get worker's rating
        reviews = Review.objects.filter(reviewee=user)
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        
        # Get nearby jobs (simplified - you can add location-based filtering)
        nearby_jobs = JobRequest.objects.filter(
            status='pending'
        ).exclude(
            worker=user
        ).order_by('-created_at')[:4]
        
        nearby_jobs_data = []
        for job in nearby_jobs:
            nearby_jobs_data.append({
                'id': job.id,
                'title': job.title,
                'client': job.client.full_name,
                'location': job.location,
                'distance': self.calculate_distance(user, job),
                'budget': f"KES {int(job.budget):,}" if job.budget else 'N/A',
                'urgency': job.urgency,
                'posted': self.get_time_ago(job.created_at),
                'category': job.category
            })
        
        # Get recent applications
        recent_applications = proposals.order_by('-created_at')[:3]
        recent_applications_data = []
        for proposal in recent_applications:
            recent_applications_data.append({
                'id': proposal.id,
                'job_title': proposal.job.title,
                'client': proposal.job.client.full_name,
                'status': 'accepted' if proposal.is_selected else 'pending',
                'applied_date': proposal.created_at.strftime('%b %d, %Y'),
                'budget': f"KES {int(proposal.proposed_price):,}"
            })
        
        # Get ongoing projects
        ongoing_projects_list = proposals.filter(
            is_selected=True,
            job__status='in_progress'
        ).select_related('job', 'negotiation')[:3]
        
        ongoing_projects_data = []
        for proposal in ongoing_projects_list:
            progress = 0
            if hasattr(proposal, 'negotiation'):
                progress = proposal.negotiation.progress_percentage or 0
            
            ongoing_projects_data.append({
                'id': proposal.job.id,
                'title': proposal.job.title,
                'client': proposal.job.client.full_name,
                'progress': progress,
                'start_date': proposal.created_at.strftime('%b %d, %Y'),
                'budget': f"KES {int(proposal.proposed_price):,}"
            })
        
        return Response({
            'stats': {
                'open_projects': open_projects,
                'proposals_submitted': proposals_submitted,
                'ongoing_projects': ongoing_projects,
                'completed_projects': completed_projects,
                'rating': round(avg_rating, 1),
                'total_earnings': f"KES {int(total_earnings):,}"
            },
            'nearby_jobs': nearby_jobs_data,
            'recent_applications': recent_applications_data,
            'ongoing_projects': ongoing_projects_data
        })
    
    def calculate_distance(self, worker, job):
        """Calculate distance between worker and job (simplified)"""
        # This is a placeholder - implement actual distance calculation
        # using worker.latitude/longitude and job.latitude/longitude
        if worker.latitude and job.latitude:
            # Simple approximation (you can use geopy or haversine formula)
            return f"{abs(worker.latitude - job.latitude) * 111:.1f} km"
        return "Distance unknown"
    
    def get_time_ago(self, date):
        """Convert datetime to time ago string"""
        now = timezone.now()
        diff = now - date
        
        if diff.days > 7:
            return date.strftime('%b %d, %Y')
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
        
        
# jobs/views.py - Fixed AdminDashboardStatsView with proper type conversion

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from users.models import User
from jobs.models import JobRequest
from proposals.models import Proposal
from negotiations.models import Negotiation, NegotiationMessage
from reviews.models import Review


class AdminDashboardStatsView(APIView):
    """Get comprehensive admin dashboard statistics"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        # Date ranges
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # ==================== USER STATISTICS ====================
        total_users = User.objects.count()
        total_clients = User.objects.filter(role='client').count()
        total_workers = User.objects.filter(role='worker').count()
        pending_workers = User.objects.filter(role='worker', is_active=False).count()
        active_workers = User.objects.filter(role='worker', is_active=True).count()
        new_users_week = User.objects.filter(date_joined__date__gte=week_ago).count()
        
        # ==================== JOB STATISTICS ====================
        total_jobs = JobRequest.objects.count()
        pending_jobs = JobRequest.objects.filter(status='pending').count()
        active_jobs = JobRequest.objects.filter(status__in=['accepted', 'in_progress']).count()
        completed_jobs = JobRequest.objects.filter(status='completed').count()
        cancelled_jobs = JobRequest.objects.filter(status='cancelled').count()
        
        # Jobs by category
        jobs_by_category = JobRequest.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Jobs by urgency
        jobs_by_urgency = JobRequest.objects.values('urgency').annotate(
            count=Count('id')
        )
        
        jobs_this_week = JobRequest.objects.filter(created_at__date__gte=week_ago).count()
        jobs_this_month = JobRequest.objects.filter(created_at__date__gte=month_ago).count()
        
        # ==================== PROPOSAL STATISTICS ====================
        total_proposals = Proposal.objects.count()
        accepted_proposals = Proposal.objects.filter(is_selected=True).count()
        avg_proposals_per_job = total_proposals / total_jobs if total_jobs > 0 else 0
        avg_proposal_price = Proposal.objects.filter(
            is_selected=True
        ).aggregate(avg=Avg('proposed_price'))['avg'] or 0
        
        # Convert Decimal to float
        if avg_proposal_price:
            avg_proposal_price = float(avg_proposal_price)
        
        # ==================== REVENUE STATISTICS ====================
        total_revenue_decimal = Proposal.objects.filter(
            is_selected=True
        ).aggregate(total=Sum('proposed_price'))['total'] or Decimal(0)
        
        # Revenue this month - using created_at instead of updated_at
        revenue_this_month_decimal = Proposal.objects.filter(
            is_selected=True,
            created_at__date__gte=month_ago
        ).aggregate(total=Sum('proposed_price'))['total'] or Decimal(0)
        
        # Convert Decimal to float for calculations
        total_revenue = float(total_revenue_decimal)
        revenue_this_month = float(revenue_this_month_decimal)
        
        platform_commission_rate = 0.10
        total_commission = total_revenue * platform_commission_rate
        monthly_commission = revenue_this_month * platform_commission_rate
        
        # ==================== NEGOTIATION STATISTICS ====================
        total_negotiations = Negotiation.objects.count()
        active_negotiations = Negotiation.objects.filter(is_active=True, project_status='negotiating').count()
        in_progress_projects = Negotiation.objects.filter(project_status='in_progress').count()
        completed_projects = Negotiation.objects.filter(project_status='completed').count()
        avg_progress = Negotiation.objects.filter(
            project_status='in_progress'
        ).aggregate(avg=Avg('progress_percentage'))['avg'] or 0
        
        if avg_progress:
            avg_progress = float(avg_progress)
        
        # ==================== MESSAGE STATISTICS ====================
        total_messages = NegotiationMessage.objects.filter(is_system_message=False).count()
        milestone_messages = NegotiationMessage.objects.filter(message_type='milestone').count()
        
        # ==================== REVIEW STATISTICS ====================
        total_reviews = Review.objects.count()
        avg_rating = Review.objects.aggregate(avg=Avg('rating'))['avg'] or 0
        
        if avg_rating:
            avg_rating = float(avg_rating)
        
        # Rating distribution
        five_star_reviews = Review.objects.filter(rating=5).count()
        four_star_reviews = Review.objects.filter(rating=4).count()
        three_star_reviews = Review.objects.filter(rating=3).count()
        two_star_reviews = Review.objects.filter(rating=2).count()
        one_star_reviews = Review.objects.filter(rating=1).count()
        
        return Response({
            'users': {
                'total': total_users,
                'clients': total_clients,
                'workers': total_workers,
                'pending_workers': pending_workers,
                'active_workers': active_workers,
                'new_this_week': new_users_week,
            },
            'jobs': {
                'total': total_jobs,
                'pending': pending_jobs,
                'active': active_jobs,
                'completed': completed_jobs,
                'cancelled': cancelled_jobs,
                'this_week': jobs_this_week,
                'this_month': jobs_this_month,
                'by_category': list(jobs_by_category),
                'by_urgency': list(jobs_by_urgency),
            },
            'proposals': {
                'total': total_proposals,
                'accepted': accepted_proposals,
                'avg_per_job': round(avg_proposals_per_job, 1),
                'avg_price': round(avg_proposal_price, 2) if avg_proposal_price else 0,
            },
            'revenue': {
                'total': round(total_revenue, 2),
                'this_month': round(revenue_this_month, 2),
                'platform_commission': round(total_commission, 2),
                'monthly_commission': round(monthly_commission, 2),
            },
            'negotiations': {
                'total': total_negotiations,
                'active': active_negotiations,
                'in_progress': in_progress_projects,
                'completed': completed_projects,
                'avg_progress': round(avg_progress, 1) if avg_progress else 0,
            },
            'messages': {
                'total': total_messages,
                'milestone_updates': milestone_messages,
            },
            'reviews': {
                'total': total_reviews,
                'avg_rating': round(avg_rating, 1) if avg_rating else 0,
                'distribution': {
                    '5_star': five_star_reviews,
                    '4_star': four_star_reviews,
                    '3_star': three_star_reviews,
                    '2_star': two_star_reviews,
                    '1_star': one_star_reviews,
                }
            }
        })