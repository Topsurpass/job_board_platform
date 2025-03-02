from rest_framework import viewsets, filters, status
from .models import Job, Industry, Category
from applications.models import Application
from applications.serializers import ApplicationSerializer
from .serializers import IndustrySerializer, JobSerializer, CategorySerializer
from .permissions import ReadOnlyModifyByAdminEmployer, ReadOnlyAdminModify
from .pagination import CustomPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from collections import defaultdict
from django.core.paginator import Paginator
from django.db.models import F, Q


logger = logging.getLogger(__name__)

class IndustryViewSet(viewsets.ModelViewSet):
    """API endpoint for industries with paginated jobs."""
    queryset = Industry.objects.all().order_by('-created_at')
    serializer_class = IndustrySerializer
    permission_classes = [ReadOnlyAdminModify]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @swagger_auto_schema(
        operation_summary="List Industries",
        operation_description="Retrieve a paginated list of industries. All users have access",
        responses={200: IndustrySerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create new Industry",
        operation_description="API that allows only admins create new industry.",
        request_body=IndustrySerializer,
        responses={
            201: openapi.Response("Created submitted successfully.", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"message": openapi.Schema(type=openapi.TYPE_STRING)})),
            400: openapi.Response("Validation error (e.g., already created).", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"error": openapi.Schema(type=openapi.TYPE_STRING)})),
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve an industry",
        operation_description="Get detailed information about a specific industry.",
        responses={200: IndustrySerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update an industry",
        operation_description="Modify an existing industry. Only admins have privilege.",
        request_body=IndustrySerializer,
        responses={200: IndustrySerializer, 400: "Bad Request"}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially Update an industry",
        operation_description="Modify certain fields of an existing industry. Only admins can perform this action.",
        request_body=IndustrySerializer,
        responses={200: IndustrySerializer, 400: "Bad Request"}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Delete an industry",
        operation_description="Remove an industry from the system with its jobs and categories. Only admins have privilege.",
        responses={204: "No Content", 403: "Forbidden"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Get all job jobs in a specific industry",
        operation_description="Retrieve a paginated list of jobs under a specific industry (Authorized and Unauthorized user can access).",
        responses={
            200: JobSerializer(many=True),
            404: "Industry not found.",
            500: "Server error."
        }
    )
    @action(detail=True, methods=["get"], url_path="jobs")
    def get_industry_jobs(self, request, pk=None):
        """Get paginated jobs for a specific industry."""
        try:
            industry = self.get_object()
            jobs = Job.objects.filter(industry=industry).order_by("-posted_at")
            paginator = CustomPagination()
            paginated_jobs = paginator.paginate_queryset(jobs, request)
            serializer = JobSerializer(paginated_jobs, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Industry.DoesNotExist:
            return Response({"error": "Industry not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Get all job categories in a specific industry",
        operation_description="Retrieve a paginated list of job categories under a specific industry (Authorized and Unauthorized user can access).",
        responses={
            200: JobSerializer(many=True),
            404: "Industry not found.",
            500: "Server error."
        }
    )
    @action(detail=True, methods=["get"], url_path="categories")
    def get_industry_categories(self, request, pk=None):
        """Retrieve all categories under a specific industry."""
        try:
            industry = self.get_object()
            categories = Category.objects.filter(industry=industry).order_by('-created_at')
            paginator = CustomPagination()
            paginated_category = paginator.paginate_queryset(categories, request)
            serializer = CategorySerializer(paginated_category, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Industry.DoesNotExist:
            return Response({"error": "Industry not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CategoryViewSet(viewsets.ModelViewSet):
    """API for creating and modifying categories"""
    queryset = Category.objects.all().order_by('-created_at')
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    permission_classes = [ReadOnlyAdminModify]
    search_fields = ['name']
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @swagger_auto_schema(
        operation_summary="List Categories",
        operation_description="Retrieve a paginated list of categories. All users have access",
        responses={200: CategorySerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create new Category",
        operation_description="API that allows only admins create new category.",
        request_body=CategorySerializer,
        responses={
            201: openapi.Response("Created submitted successfully.", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"message": openapi.Schema(type=openapi.TYPE_STRING)})),
            400: openapi.Response("Validation error (e.g., already created).", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"error": openapi.Schema(type=openapi.TYPE_STRING)})),
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a category",
        operation_description="Get detailed information about a specific category.",
        responses={200: CategorySerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update a category",
        operation_description="Modify an existing category. Only admins have privilege.",
        request_body=CategorySerializer,
        responses={200: CategorySerializer, 400: "Bad Request"}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially Update a category",
        operation_description="Modify certain fields of an existing category. Only admins can perform this action.",
        request_body=CategorySerializer,
        responses={200: CategorySerializer, 400: "Bad Request"}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Delete a category",
        operation_description="Remove a category from the system. Only admins have privilege.",
        responses={204: "No Content", 403: "Forbidden"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Get all jobs in a specific category",
        operation_description="Retrieve a paginated list of job under a specific category (Authorized and Unauthorized users can access).",
        responses={
            200: JobSerializer(many=True),
            404: "Category not found.",
            500: "Server error."
        }
    )
    @action(detail=True, methods=["get"], url_path="jobs")
    def get_category_jobs(self, request, pk=None):
        """Retrieve all jobs under a specific industry category."""
        try:
            category = self.get_object()
            jobs = Job.objects.filter(category=category).order_by('-posted_at')
            paginator = CustomPagination()
            paginated_jobs = paginator.paginate_queryset(jobs, request)
            serializer = JobSerializer(paginated_jobs, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Category.DoesNotExist:
            return Response({"error": "Category not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class JobViewSet(viewsets.ModelViewSet):
    """API endpoint for jobs with optimized categorized-jobs endpoint."""
    queryset = Job.objects.select_related("industry", "posted_by").only(
        "id", "title", "industry__name", "location", "type", "posted_by__id"
    ).order_by("-posted_at")
    
    serializer_class = JobSerializer
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    permission_classes = [ReadOnlyModifyByAdminEmployer]
    search_fields = ["title", "type", "location", "industry__name"]

    def perform_create(self, serializer):
        """Make the authenticated user the one who posted the job"""
        serializer.save(posted_by=self.request.user)

    @swagger_auto_schema(
        operation_summary="List Jobs",
        operation_description="Retrieve a paginated list of jobs. All users have access",
        responses={200: JobSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create new Job",
        operation_description="API that allows only admins and employer create new job.",
        request_body=JobSerializer,
        responses={
            201: openapi.Response("Created submitted successfully.", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"message": openapi.Schema(type=openapi.TYPE_STRING)})),
            400: openapi.Response("Validation error (e.g., already created).", schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={"error": openapi.Schema(type=openapi.TYPE_STRING)})),
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a job",
        operation_description="Get detailed information about a specific job.",
        responses={200: JobSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update a job",
        operation_description="Modify an existing job. Only admins and employer have privilege. Employer can only update their own job",
        request_body=JobSerializer,
        responses={200: JobSerializer, 400: "Bad Request"}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially Update a job",
        operation_description="Modify certain fields of an existing job. Only admins and employer have privilege. Employer can only update their own job",
        request_body=JobSerializer,
        responses={200: JobSerializer, 400: "Bad Request"}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Delete a job",
        operation_description="Remove a job from the system. Only admins and employer have privilege. Employer can only update their own job",
        responses={204: "No Content", 403: "Forbidden"}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    def _paginate_queryset(self, request, job_list, category):
        """Helper method to paginate job listings"""
        page_size = int(request.GET.get("page_size", 10))
        page_number = int(request.GET.get("page", 1))
        paginator = Paginator(job_list, page_size)
        page = paginator.get_page(page_number)

        return {
            "total_count": paginator.count,
            "jobs": list(page),
            "pagination": {
                "next": page.next_page_number() if page.has_next() else None,
                "previous": page.previous_page_number() if page.has_previous() else None,
            },
        }
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Get all job categories.",
        operation_description="Retrieve a paginated jobs, categorized and filtered dynamically by location, type, or industry. (Authorized and Unauthorized users can access).",
        responses={
            200: JobSerializer(many=True),
            404: "Invalid category. Use location, type, or industry.",
            500: "No Category matches the given query."
        }
    )
    @action(detail=False, methods=["get"], url_path="categorized-jobs")
    def get_categorized_jobs(self, request):
        """Get jobs categorized and filtered dynamically by location, type, or industry."""
        category = request.GET.get("category")
        category_filter = request.GET.get("filter")
        search_query = request.GET.get("search", "").strip()

        if category not in ["location", "type", "industry"]:
            return Response({"error": "Invalid category. Use location, type, or industry."}, status=status.HTTP_400_BAD_REQUEST)

        jobs = Job.objects.annotate(industry_name=F("industry__name"))
        if search_query:
            jobs = jobs.filter(
                Q(title__icontains=search_query) |
                Q(industry__name__icontains=search_query) |
                Q(location__icontains=search_query) |
                Q(type__icontains=search_query)
            )

        category_field = "industry_name" if category == "industry" else category
        jobs = jobs.values("id", "title", "industry_name", "location", "type", "wage").order_by("-posted_at")
        job_groups = defaultdict(list)
        for job in jobs:
            job_groups[job[category_field] or "Other"].append(job)

        if category_filter:
            job_groups = {category_filter: job_groups.get(category_filter, [])}

        paginated_data = {key: self._paginate_queryset(request, job_list, category) for key, job_list in job_groups.items()}
        return Response(paginated_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='get',
        operation_summary="Get all job applicants.",
        operation_description="Retrieve a paginated applicants for a specified job.",
        responses={
            200: ApplicationSerializer(many=True),
            403: "You do not have permission to perform this action.",
            404: "Job not found.",
            500: "Server error."
        }
    )
    @action(detail=True, methods=["get"], url_path="applicants")
    def get_applicants(self, request, pk=None):
        """Optimized applicants retrieval with caching."""
        job = self.get_object()
        if not request.user.is_authenticated or (not request.user.is_superuser and job.posted_by != request.user):
            return Response(
                {"detail": "You do not have permission to perform this action."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        cache_key = f"job_{pk}_applicants"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        applicants = Application.objects.filter(job=job).select_related("applicant")
        paginator = CustomPagination()
        paginated_applicants = paginator.paginate_queryset(applicants, request)
        serializer = ApplicationSerializer(paginated_applicants, many=True)
        response_data = {
            "applicants": serializer.data
        }
        cache.set(cache_key, response_data, timeout=60 * 10)
        return paginator.get_paginated_response(response_data)