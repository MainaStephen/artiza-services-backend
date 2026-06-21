from rest_framework import generics, status, permissions
from rest_framework.response import Response
from .models import ArtisanApplication, ArtisanDocument
from .serializers import ArtisanApplicationSerializer,ArtisanApplicationStatusUpdateSerializer


class ArtisanApplicationCreateView(generics.CreateAPIView):
    serializer_class = ArtisanApplicationSerializer
    queryset = ArtisanApplication.objects.all()
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        files = self.request.FILES.getlist("documents")

        application = serializer.save()

        # 🔥 THIS IS WHAT YOU WERE MISSING
        for file in files:
            ArtisanDocument.objects.create(
                application=application,
                file=file
            )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        return Response(
            {
                "message": "Application submitted successfully",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )
        
        
        
class AdminArtisanApplicationsView(generics.ListAPIView):
    serializer_class = ArtisanApplicationSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        
        user = self.request.user
        
        if user.role == "admin":
            return ArtisanApplication.objects.all().order_by("-created_at")
        
        
        return ArtisanApplication.objects.none()
    
    




class ArtisanApplicationStatusUpdateView(generics.UpdateAPIView):
    queryset = ArtisanApplication.objects.all()
    serializer_class = ArtisanApplicationStatusUpdateSerializer  # Use the dedicated serializer
    permission_classes = [permissions.IsAdminUser]
    
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": f"Application status updated to {serializer.validated_data['application_status']}",
                "status": serializer.validated_data['application_status']
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
    