from django.shortcuts import render
from .serializers import CustomTokenObtainPairSerializer, RegisterUserSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .models import User
from .serializers import WorkerCreateSerializer, WorkerActivationSerializer, RegisterUserSerializer, UserProfileSerializer
from .emails import send_worker_activation_email, send_welcome_email
from .tokens import activation_token
from jobs.models import JobRequest
from rest_framework import permissions
# Create your views here.

class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    

class RegisterUserView(generics.CreateAPIView):
    serializer_class = RegisterUserSerializer
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "Registration successful.",
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)








# views.py - The CreateWorkerView remains the same since serializer handles skill
class CreateWorkerView(generics.CreateAPIView):
    """
    Admin creates a worker account with skill.
    An activation email is sent to the worker's email.
    """
    serializer_class = WorkerCreateSerializer
    permission_classes = [IsAdminUser]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the worker (inactive) - skill is set here
        user = serializer.save()
        
        # Generate activation token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = activation_token.make_token(user)
        
        # Create activation link
        from django.conf import settings
        activation_link = f"{settings.FRONTEND_URL}/activate-worker/{uid}/{token}/"
        
        # Send activation email
        try:
            send_worker_activation_email({
                'user': user,
                'activation_url': activation_link
            })
        except Exception as e:
            # Delete the user if email fails
            user.delete()
            return Response(
                {"error": f"Failed to send activation email: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(
            {
                "message": "Worker account created successfully. An activation email has been sent to the worker.",
                "user": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "skill": user.skill,
                    "role": user.role
                }
            },
            status=status.HTTP_201_CREATED
        )
        


class ActivateWorkerView(APIView):
    """
    Worker activates their account by setting a password and location
    """
    permission_classes = [AllowAny]
    
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid, role='worker')
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"error": "Invalid activation link."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check token validity
        if not activation_token.check_token(user, token):
            return Response(
                {"error": "Activation link has expired or is invalid."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already active
        if user.is_active:
            return Response(
                {"message": "Account is already activated. Please login."},
                status=status.HTTP_200_OK
            )
        
        # Validate input data
        serializer = WorkerActivationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Activate the account
        user.set_password(serializer.validated_data['password'])
        user.is_active = True
        user.agree_to_terms = True
        user.terms_accepted_at = timezone.now()
        
        # Update skill if provided
        if serializer.validated_data.get('skill'):
            user.skill = serializer.validated_data['skill']
        
        # Update location if provided
        if serializer.validated_data.get('latitude') is not None:
            user.latitude = serializer.validated_data['latitude']
            user.longitude = serializer.validated_data['longitude']
        
        if serializer.validated_data.get('address'):
            user.address = serializer.validated_data['address']
        
        user.save()
        
        # Send welcome email
        try:
            send_welcome_email({'user': user})
        except Exception as e:
            print(f"Welcome email failed: {e}")
        
        return Response(
            {
                "message": "Account activated successfully! You can now login.",
                "email": user.email,
                "skill": user.skill,
                "has_location": user.latitude is not None
            },
            status=status.HTTP_200_OK
        )

# ✅ Client registration (immediate activation)
class RegisterClientView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "Registration successful. You can now login.",
                    "user": {
                        "id": user.id,
                        "full_name": user.full_name,
                        "email": user.email,
                        "role": user.role
                    }
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Get pending worker applications (for admin)
class PendingWorkerApplicationsView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        pending_workers = User.objects.filter(
            role='worker',
            is_active=False,
            date_joined__gte=timezone.now() - timezone.timedelta(days=7)  # Last 7 days
        ).exclude(email__isnull=True)
        
        applications = []
        for worker in pending_workers:
            applications.append({
                "id": worker.id,
                "full_name": worker.full_name,
                "email": worker.email,
                "phone_number": worker.phone_number,
                "created_at": worker.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "pending"
            })
        
        return Response({
            "count": len(applications),
            "applications": applications
        })


# ✅ Resend activation email (admin action)
class ResendActivationEmailView(APIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, role='worker', is_active=False)
        except User.DoesNotExist:
            return Response(
                {"error": "Worker not found or already active."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate new activation token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = activation_token.make_token(user)
        
        from django.conf import settings
        activation_link = f"{settings.FRONTEND_URL}/activate-worker/{uid}/{token}/"
        
        try:
            send_worker_activation_email({
                'user': user,
                'activation_url': activation_link
            })
        except Exception as e:
            return Response(
                {"error": f"Failed to send email: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({"message": "Activation email resent successfully."})
    
    
# users/views.py - Add these views

class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """Change user password"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        if not user.check_password(current_password):
            return Response(
                {"error": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(new_password) < 6:
            return Response(
                {"error": "Password must be at least 6 characters"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response(
            {"message": "Password changed successfully"},
            status=status.HTTP_200_OK
        )

# users/views.py - Updated with real rating calculations

from django.db.models import Avg, Count, Sum
from reviews.models import Review, UserRating


class ClientStatsView(generics.GenericAPIView):
    """Get client statistics with real rating from reviews"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        jobs = JobRequest.objects.filter(client=user)
        
        total = jobs.count()
        active = jobs.filter(status__in=['accepted', 'in_progress']).count()
        completed = jobs.filter(status='completed').count()
        
        # Calculate total spent from accepted proposals
        from proposals.models import Proposal
        accepted_proposals = Proposal.objects.filter(
            job__client=user, 
            is_selected=True
        )
        total_spent = sum(p.proposed_price for p in accepted_proposals if p.proposed_price)
        
        # Get real rating from reviews where client is the reviewee
        reviews = Review.objects.filter(reviewee=user)
        rating_avg = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        review_count = reviews.count()
        
        # Get star distribution
        star_distribution = {
            '5_star': reviews.filter(rating=5).count(),
            '4_star': reviews.filter(rating=4).count(),
            '3_star': reviews.filter(rating=3).count(),
            '2_star': reviews.filter(rating=2).count(),
            '1_star': reviews.filter(rating=1).count(),
        }
        
        return Response({
            'total': total,
            'active': active,
            'completed': completed,
            'total_spent': float(total_spent),
            'rating': round(rating_avg, 1),
            'reviews': review_count,
            'star_distribution': star_distribution
        })


class WorkerStatsView(generics.GenericAPIView):
    """Get worker statistics with real rating from reviews"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        from proposals.models import Proposal
        
        proposals = Proposal.objects.filter(worker=user)
        
        applied = proposals.count()
        in_progress = proposals.filter(
            is_selected=True, 
            job__status__in=['accepted', 'in_progress']
        ).count()
        completed = proposals.filter(job__status='completed').count()
        
        # Calculate total earned from completed jobs
        completed_proposals = proposals.filter(job__status='completed', is_selected=True)
        total_earned = sum(p.proposed_price for p in completed_proposals if p.proposed_price)
        
        # Get real rating from reviews where worker is the reviewee
        reviews = Review.objects.filter(reviewee=user)
        rating_avg = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        review_count = reviews.count()
        
        # Get star distribution
        star_distribution = {
            '5_star': reviews.filter(rating=5).count(),
            '4_star': reviews.filter(rating=4).count(),
            '3_star': reviews.filter(rating=3).count(),
            '2_star': reviews.filter(rating=2).count(),
            '1_star': reviews.filter(rating=1).count(),
        }
        
        # Get rating breakdown by category (if available)
        rating_breakdown = {
            'communication': reviews.aggregate(avg=Avg('communication_rating'))['avg'] or 0,
            'quality': reviews.aggregate(avg=Avg('quality_rating'))['avg'] or 0,
            'punctuality': reviews.aggregate(avg=Avg('punctuality_rating'))['avg'] or 0,
        }
        
        return Response({
            'applied': applied,
            'in_progress': in_progress,
            'completed': completed,
            'total_earned': float(total_earned),
            'rating': round(rating_avg, 1),
            'reviews': review_count,
            'star_distribution': star_distribution,
            'rating_breakdown': rating_breakdown
        })


class UserRatingDetailView(generics.RetrieveAPIView):
    """Get detailed rating information for a user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, user_id=None):
        target_user_id = user_id or request.user.id
        target_user = get_object_or_404(User, id=target_user_id)
        
        reviews = Review.objects.filter(reviewee=target_user)
        
        # Calculate statistics
        total_reviews = reviews.count()
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        
        # Get recent reviews
        recent_reviews = reviews.order_by('-created_at')[:5]
        
        from reviews.serializers import ReviewSerializer
        recent_reviews_data = ReviewSerializer(recent_reviews, many=True, context={'request': request}).data
        
        return Response({
            'user': {
                'id': target_user.id,
                'full_name': target_user.full_name,
                'role': target_user.role,
                'profile_picture': target_user.profile_picture.url if target_user.profile_picture else None
            },
            'rating_summary': {
                'average_rating': round(avg_rating, 1),
                'total_reviews': total_reviews,
                '5_star': reviews.filter(rating=5).count(),
                '4_star': reviews.filter(rating=4).count(),
                '3_star': reviews.filter(rating=3).count(),
                '2_star': reviews.filter(rating=2).count(),
                '1_star': reviews.filter(rating=1).count(),
            },
            'recent_reviews': recent_reviews_data
        })


class UpdateUserRatingView(generics.GenericAPIView):
    """Manually update user rating summary (admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        from reviews.models import UserRating
        
        # Update all users' ratings
        users = User.objects.all()
        updated_count = 0
        
        for user in users:
            rating_obj, created = UserRating.objects.get_or_create(user=user)
            rating_obj.update_ratings()
            updated_count += 1
        
        return Response({
            'message': f'Updated ratings for {updated_count} users',
            'updated_count': updated_count
        })
        
        
        
# users/views.py - Add these views for admin user management

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import User
from .serializers import UserSerializer, WorkerCreateSerializer
from .emails import send_worker_activation_email
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from .tokens import activation_token


class AdminAllUsersView(APIView):
    """Get all users with filtering for admin panel"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        role = request.query_params.get('role', None)
        status_filter = request.query_params.get('status', None)
        search = request.query_params.get('search', None)
        
        users = User.objects.all().order_by('-date_joined')
        
        # Filter by role
        if role and role != 'all':
            users = users.filter(role=role)
        
        # Filter by active status
        if status_filter and status_filter != 'all':
            if status_filter == 'active':
                users = users.filter(is_active=True)
            elif status_filter == 'inactive':
                users = users.filter(is_active=False)
        
        # Search by name, email, or phone
        if search:
            users = users.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone_number__icontains=search)
            )
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        total = users.count()
        paginated_users = users[start:end]
        
        serializer = UserSerializer(paginated_users, many=True, context={'request': request})
        
        return Response({
            'users': serializer.data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        })


class AdminUserDetailView(APIView):
    """Get, update, or delete a specific user"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)
    
    def patch(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user.delete()
        return Response({'message': 'User deleted successfully'}, status=status.HTTP_200_OK)


class AdminCreateWorkerView(APIView):
    """Admin creates a new worker account"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        serializer = WorkerCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate activation token
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = activation_token.make_token(user)
            
            from django.conf import settings
            activation_link = f"{settings.FRONTEND_URL}/activate-worker/{uid}/{token}/"
            
            try:
                send_worker_activation_email({
                    'user': user,
                    'activation_url': activation_link
                })
            except Exception as e:
                user.delete()
                return Response(
                    {"error": f"Failed to send activation email: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response({
                'message': 'Worker created successfully. Activation email sent.',
                'user': UserSerializer(user, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminToggleUserStatusView(APIView):
    """Activate or deactivate a user"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        status_text = "activated" if user.is_active else "deactivated"
        
        return Response({
            'success': True,
            'message': f'User {user.full_name} has been {status_text}.',
            'is_active': user.is_active
        })


class AdminMakeAdminView(APIView):
    """Toggle admin status for a user"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        
        # Prevent self-demotion from admin
        if request.user.id == user.id and user.is_staff:
            return Response({
                'error': 'You cannot remove your own admin privileges.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_staff = not user.is_staff
        if user.is_staff:
            user.role = 'admin'
        else:
            if user.role == 'admin':
                user.role = 'client'  # Default to client when removing admin
        user.save()
        
        role_text = "granted admin privileges to" if user.is_staff else "removed admin privileges from"
        
        return Response({
            'success': True,
            'message': f'You have {role_text} {user.full_name}.',
            'is_admin': user.is_staff
        })