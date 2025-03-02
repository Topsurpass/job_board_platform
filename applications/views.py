from rest_framework import viewsets, filters, serializers, status
from .models import Application
from .serializers import ApplicationSerializer
from jobs.permissions import ReadCreateOnlyAdminModify
from jobs.pagination import CustomPagination
from rest_framework.response import Response
from jobs.models import Job
from .tasks.email_tasks import send_job_application_email

class ApplicationViewSet(viewsets.ModelViewSet):
    """API endpoint that allows user to submit application"""
    queryset = Application.objects.all().order_by('-applied_at')
    serializer_class = ApplicationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['job__title', 'job__company', 'job__industry__name', 'status']
    permission_classes = [ReadCreateOnlyAdminModify]
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        """Assign the logged-in user as the applicant and update application status"""
        job_id = self.request.data.get("job")

        if not job_id:
            raise serializers.ValidationError({"job": "This field is required."})
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise serializers.ValidationError({"job": "Invalid job ID."})
        applicant = self.request.user

        if Application.objects.filter(job=job, applicant=applicant).exists():
            raise serializers.ValidationError({"error": "You have already applied for this job."})

        serializer.save(job=job, applicant=applicant, status="submitted")
        send_job_application_email.delay(
            recipient_email=applicant.email,
            first_name=applicant.first_name,
            job_title=job.title,
            company_name=job.company
        )
        return Response({"message": "Account created successfully. A welcome email has been sent."}, status=status.HTTP_201_CREATED)

