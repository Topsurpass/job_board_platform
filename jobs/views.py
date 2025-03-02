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
        manual_parameters=[
            openapi.Parameter(
                "category",
                openapi.IN_QUERY,
                description="Category to filter jobs by (industry, location, or type)",
                type=openapi.TYPE_STRING,
                enum=["industry", "location", "type"],
                required=True,
            ),
            openapi.Parameter(
                "filter",
                openapi.IN_QUERY,
                description="Specific category value to filter (e.g., Lagos, Full-Time, Technology)",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search for jobs by title, industry, location, or type",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number for pagination",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="Number of jobs per page (default: 10)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
        ],
        responses={
            200: openapi.Response(
                "Jobs categorized and paginated successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "category_name": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "total_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "jobs": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                            "title": openapi.Schema(type=openapi.TYPE_STRING),
                                            "industry_name": openapi.Schema(type=openapi.TYPE_STRING),
                                            "location": openapi.Schema(type=openapi.TYPE_STRING),
                                            "type": openapi.Schema(type=openapi.TYPE_STRING),
                                            "wage": openapi.Schema(type=openapi.TYPE_NUMBER),
                                        },
                                    ),
                                ),
                                "pagination": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "next": openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                        "previous": openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    },
                                ),
                            },
                        )
                    },
                ),
            ),
            400: "Invalid request (e.g., missing required parameters)",
        },
    )

    @action(detail=False, methods=["get"], url_path="categorized-jobs")
    def get_categorized_jobs(self, request):
        """Get jobs categorized and filtered dynamically by location, type, or industry."""
        category = request.GET.get("category")  # Can be "location", "type", or "industry"
        category_filter = request.GET.get("filter")  # Specific value to filter by
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

        # Convert "industry" to match annotation name
        category_field = "industry_name" if category == "industry" else category
        jobs = jobs.values("id", "title", "industry_name", "location", "type", "wage").order_by("-posted_at")

        job_groups = defaultdict(list)
        for job in jobs:
            job_groups[job[category_field] or "Other"].append(job)

        if category_filter:
            job_groups = {category_filter: job_groups.get(category_filter, [])}

        paginated_data = {key: self._paginate_queryset(request, job_list, category) for key, job_list in job_groups.items()}
        return Response(paginated_data, status=status.HTTP_200_OK)

   
    @action(detail=True, methods=["get"], url_path="applicants")
    def get_applicants(self, request, pk=None):
        """Optimized applicants retrieval with caching."""
        job = self.get_object()
        if not request.user.is_authenticated or (not request.user.is_superuser and job.posted_by != request.user):
            return Response(
                {"detail": "Permission denied."}, 
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
            "count": applicants.count(),
            "applicants": serializer.data
        }
        cache.set(cache_key, response_data, timeout=60 * 10)
        return paginator.get_paginated_response(response_data)

