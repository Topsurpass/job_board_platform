from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, filters, serializers, status
from .models import Application
from .serializers import ApplicationSerializer, ApplicationBodySerializer
from .permissions import ReadCreateOnlyAdminModify
from jobs.pagination import CustomPagination
from rest_framework.response import Response
from jobs.models import Job
from .tasks.email_tasks import send_job_application_email

class ApplicationViewSet(viewsets.ModelViewSet):
    """API endpoint that allows users to submit and manage job applications."""
    queryset = Application.objects.all().order_by('-applied_at')
    serializer_class = ApplicationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['job__title', 'job__company', 'job__industry__name', 'status']
    permission_classes = [ReadCreateOnlyAdminModify]
    pagination_class = CustomPagination

    @swagger_auto_schema(
        operation_summary="List all job aplications applied by user. Employers only see job applications for jobs they posted",
        operation_description="Retrieve a paginated list of job applications based on user role. Users get to see all their applications, Employers only see list of applications for jobs posted by them",
        responses={200: ApplicationSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific job Application applied to",
        operation_description="Get detailed information about a specific job a user applied to.",
        responses={200: ApplicationSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Apply for a  job",
        operation_description="Submit a new job application by a user. A user can only apply once per job.",
        request_body=ApplicationBodySerializer,
        responses={
            201: ApplicationSerializer,
            400: openapi.Response("Validation error (e.g., already applied).", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"error": openapi.Schema(type=openapi.TYPE_STRING)})),
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a Job Application",
        operation_description="Modify an existing job application. Only admins can update application status.",
        request_body=ApplicationSerializer,
        responses={200: ApplicationSerializer, 400: "Bad Request"}
    )
    def update(self, request, *args, **kwargs):
        if set(request.data.keys()) != {"status"}:
            return Response(
                {"error": "You can only update the 'status' field of an application."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially Update a Job Application",
        operation_description="Modify certain fields of an existing job application. Only admins can perform this action.",
        request_body=ApplicationSerializer,
        responses={200: ApplicationSerializer, 400: "Bad Request"}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete a Job Application",
        operation_description="Remove a job application from the system. Only admins can delete applications.",
        responses={204: "No Content", 403: "Forbidden"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Limit applications to the ones the user is allowed to see."""
        user = self.request.user

        if not user.is_authenticated:
            return Application.objects.none()
        if user.is_superuser:
            return Application.objects.all()
        if hasattr(user, "role"):
            if user.role == "employer":
                return Application.objects.filter(job__posted_by=user)
            if user.role == "user":
                return Application.objects.filter(applicant=user)
        return Application.objects.none()

    def perform_create(self, serializer):
        """Assign the logged-in user as the applicant and update application status."""
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
        return Response({"message": "Application submitted successfully. An email has been sent."}, status=status.HTTP_201_CREATED)