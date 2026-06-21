# # from django.shortcuts import render
# # from rest_framework import generics, permissions
# # from .serializers import ProposalSerializer

# # class CreateProposalView(generics.CreateAPIView):
# #     serializer_class = ProposalSerializer
# #     permission_classes = [permissions.IsAuthenticated]

# #     def perform_create(self, serializer):

# #         if self.request.user.role != "worker":
# #             raise ValueError(
# #                 "Only workers can submit proposals."
# #             )

# #         serializer.save(worker=self.request.user)



# from rest_framework import generics, permissions
# from .models import Proposal, JobRequest
# from .serializers import ProposalSerializer, WorkerProposalListSerializer

# class ProposalCreateView(generics.CreateAPIView):
#     serializer_class = ProposalSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def perform_create(self, serializer):
#         job = JobRequest.objects.get(id=self.kwargs["job_id"])

#         serializer.save(
#             worker=self.request.user,
#             job=job
#         )
        
        
# class WorkerProposalsListView(generics.ListAPIView):
#     serializer_class = WorkerProposalListSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_queryset(self):
#         return Proposal.objects.filter(worker=self.request.user)





from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Proposal, JobRequest
from .serializers import ProposalSerializer, WorkerProposalListSerializer


class ProposalCreateView(generics.CreateAPIView):
    serializer_class = ProposalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        job = get_object_or_404(JobRequest, id=self.kwargs["job_id"])
        
        # Check if job is still open
        if job.status != 'pending':
            raise serializers.ValidationError(
                "This job is no longer accepting proposals."
            )
        
        serializer.save(
            worker=self.request.user,
            job=job
        )
        
        
class WorkerProposalsListView(generics.ListAPIView):
    serializer_class = WorkerProposalListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Proposal.objects.filter(worker=self.request.user)


# Client views proposals for their job
class ClientJobProposalsListView(generics.ListAPIView):
    serializer_class = ProposalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        job_id = self.kwargs.get('job_id')
        # Verify the job belongs to this client
        job = get_object_or_404(JobRequest, id=job_id, client=self.request.user)
        return Proposal.objects.filter(job=job)


# Select/accept a proposal (sets is_selected=True for this proposal, False for others)
class SelectProposalView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, proposal_id):
        try:
            proposal = Proposal.objects.get(id=proposal_id)
        except Proposal.DoesNotExist:
            return Response(
                {"error": "Proposal not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission: only the job owner can select a proposal
        if proposal.job.client != request.user:
            return Response(
                {"error": "You don't have permission to select this proposal"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if job is still pending
        if proposal.job.status != 'pending':
            return Response(
                {"error": "This job already has an accepted proposal"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set is_selected=False for all proposals of this job
        Proposal.objects.filter(job=proposal.job).update(is_selected=False)
        
        # Set is_selected=True for this proposal
        proposal.is_selected = True
        proposal.save()
        
        # Update job status and assign worker
        job = proposal.job
        job.status = 'in_progress'
        job.worker = proposal.worker
        job.save()
        
        serializer = ProposalSerializer(proposal)
        return Response({
            "message": "Proposal selected successfully",
            "proposal": serializer.data
        })