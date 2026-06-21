from rest_framework import serializers
from .models import Proposal    
from jobs.serializer import JobRequestSerializer


class ProposalSerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(
        source="worker.full_name",
        read_only=True
    )
    worker_email = serializers.EmailField(
        source="worker.email",
        read_only=True
    )
    # Computed field to show status text
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = [
            "id",
            "job",
            "worker",
            "worker_name",
            "worker_email",
            "proposed_price",
            "estimated_days",
            "cover_letter",
            "is_selected",
            "status_display",
            "created_at",
        ]
        read_only_fields = [
            "worker",
            "is_selected",
            "job",
        ]
    
    def get_status_display(self, obj):
        if obj.is_selected:
            return "Accepted"
        # Check if any other proposal for this job is selected
        if Proposal.objects.filter(job=obj.job, is_selected=True).exists():
            return "Declined"
        return "Pending"


class WorkerProposalListSerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(
        source="worker.full_name",
        read_only=True
    )
    job = JobRequestSerializer(read_only=True)
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = [
            "id",
            "job",
            "worker",
            "worker_name",
            "proposed_price",
            "estimated_days",
            "cover_letter",
            "is_selected",
            "status_display",
            "created_at",
        ]
        read_only_fields = [
            "worker",
            "is_selected",
            "job",
        ]
    
    def get_status_display(self, obj):
        if obj.is_selected:
            return "Accepted"
        # Check if any other proposal for this job is selected
        if Proposal.objects.filter(job=obj.job, is_selected=True).exists():
            return "Declined"
        return "Pending"