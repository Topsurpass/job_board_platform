from rest_framework import viewsets, filters
from .models import Job, Category, Application
from .serializers import  CategorySerializer, JobSerializer, ApplicationSerializer
from .permissions import ReadOnlyForAllUsersModifyByAdmin, ReadCreateOnlyAdminModify
from .pagination import CustomPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from rest_framework import status



class CategoryViewSet(viewsets.ModelViewSet):
    """API endpoint that allows categories to be created, viewed, deleted or edited"""
    queryset = Category.objects.all().order_by('-created_at')
    serializer_class = CategorySerializer
    permission_classes = [ReadOnlyForAllUsersModifyByAdmin]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    @action(detail=True, methods=["get"], url_path="jobs")
    def get_jobs(self, request, pk=None):
        """
        Custom endpoint to retrieve all jobs for a specific category alongside with their count.
        """
        category = self.get_object()
        jobs = Job.objects.filter(category=category)
        count = jobs.count()
        serializer = JobSerializer(jobs, many=True)

        return Response({"count": count, "jobs": serializer.data})

class JobViewSet(viewsets.ModelViewSet):
    """API endpoint that allows jobs to be created, viewed, deleted or edited."""
    queryset = Job.objects.all().order_by("-posted_at") 
    serializer_class = JobSerializer
    permission_classes = [ReadOnlyForAllUsersModifyByAdmin]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'type', 'company', 'location', 'category__name']

    @action(detail=True, methods=["get"], url_path="applicants")
    def get_applicants(self, request, pk=None):
        """
        Custom endpoint to retrieve all applicants for a specific job along with their count.
        """
        job = self.get_object()
        if not request.user.is_authenticated and not request.user.is_superuser and job.posted_by != request.user:
            return Response(
                {"detail": "You do not have permission to view applicants for this job."},
                status=status.HTTP_403_FORBIDDEN,
        )
        cache_key = f"job_{pk}_applicants"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)
        applicants = Application.objects.filter(job=job).select_related("applicant") 
        count = applicants.count()
        serializer = ApplicationSerializer(applicants, many=True)
        response_data = {"count": count, "applicants": serializer.data}
        cache.set(cache_key, response_data, timeout=60 * 10) # 10 minutes cache

        return Response(response_data)

class ApplicationViewSet(viewsets.ModelViewSet):
    """API endpoint that allows user to submit application"""
    queryset = Application.objects.all().order_by('-applied_at')
    serializer_class = ApplicationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['job__title', 'job__company', 'job__category__name']
    permission_classes = [ReadCreateOnlyAdminModify]
    pagination_class = CustomPagination
