from rest_framework import viewsets, filters, status
from .models import Job, Industry, Category
from applications.models import Application
from applications.serializers import ApplicationSerializer, AppJobSerializer
from .serializers import IndustrySerializer, JobSerializer, CategorySerializer, CategoryIndustrySerializer
from .permissions import (
    ReadOnlyModifyByAdminEmployer,
    ReadOnlyAdminModify,
    IsAdminAndEmployer,
    IsOnlyAdmin
)
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
from django.http import Http404


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
        operation_summary="Get all jobs in a specific industry",
        operation_description="Retrieve a paginated list of jobs under a specific industry. Supports search, pagination, and page size customization.",
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number for pagination.",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="Number of jobs per page.",
                type=openapi.TYPE_INTEGER
            ),
        ],
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
        operation_description="Retrieve a paginated list of job categories under a specific industry. Supports search, pagination, and page size customization.",
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search categories by name.",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page number for pagination.",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description="Number of categories per page.",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={
            200: CategorySerializer(many=True),
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
    
    @swagger_auto_schema(
        operation_summary="Get all industries created by an admin",
        operation_description="Retrieves a paginated list of industries created by the signed-in admin.",
        responses={200: openapi.Response(
            description="Paginated response of industries",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "count": openapi.Schema(type=openapi.TYPE_INTEGER, example=10),
                    "next": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, example="http://api.example.com/industries/?page=2"),
                    "previous": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, example=None),
                    "results": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID, example="123e4567-e89b-12d3-a456-426614174000"),
                                "name": openapi.Schema(type=openapi.TYPE_STRING, example="Technology"),
                            },
                        ),
                    ),
                }
            ),
        )}
    ) 
    @action(detail=False, methods=["get"], url_path="all-industries", permission_classes=[IsOnlyAdmin])
    def get_all_industries(self, request, pk=None):
        """Get all industries created by an admin"""
        
        user = request.user
        all_industries = Industry.objects.filter(created_by=user).order_by('-created_at')
        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(all_industries, request)
        serialized_data = IndustrySerializer(result_page, many=True).data
        return paginator.get_paginated_response(serialized_data)
    
    
    @swagger_auto_schema(
        operation_summary="Get all categories grouped by industry",
        operation_description="Retrieves all categories created by the current admin, grouped under their respective industries.",
        responses={200: openapi.Response(
            description="A list of industries with their associated categories",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "count": openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
                    "next": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, example=None),
                    "previous": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, example=None),
                    "results": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "industry": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "id": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID, example="123e4567-e89b-12d3-a456-426614174000"),
                                        "name": openapi.Schema(type=openapi.TYPE_STRING, example="Technology"),
                                    },
                                ),
                                "categories": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "id": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID, example="223e4567-e89b-12d3-a456-426614174000"),
                                            "name": openapi.Schema(type=openapi.TYPE_STRING, example="Software Development"),
                                        }
                                    ),
                                ),
                            },
                        ),
                    ),
                }
            ),
        )}
    )
    @action(detail=False, methods=["get"], url_path="categories-by-industry", permission_classes=[IsOnlyAdmin])
    def get_categories_by_industry(self, request):
        """Get all categories created by the current admin and group them by industry."""
        user = request.user 
        categories = Category.objects.filter(created_by=user).select_related("industry")

        industry_categories = defaultdict(list)
        for category in categories:
            industry_categories[category.industry].append(category)

        grouped_data = []
        for industry, category_list in industry_categories.items():
            grouped_data.append({
                "industry": IndustrySerializer(industry).data,
                "categories": CategoryIndustrySerializer(category_list, many=True).data
            })

        paginator = CustomPagination()
        paginated_result = paginator.paginate_queryset(grouped_data, request)

        return paginator.get_paginated_response(paginated_result)
    
    
    @swagger_auto_schema(
        operation_summary="Get industries an employer has posted jobs under",
        operation_description="Returns the total count and a paginated list of industries an employer has posted jobs under.",
        manual_parameters=[
            openapi.Parameter(
                name="page",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="Page number for pagination"
            ),
            openapi.Parameter(
                name="page_size",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="Number of items per page"
            ),
        ],
        responses={
            200: openapi.Response(
                description="A paginated list of industries the employer has used in job postings.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "count": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total number of industries used"),
                        "next": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, nullable=True, description="URL of the next page (if any)"),
                        "previous": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, nullable=True, description="URL of the previous page (if any)"),
                        "results": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Industry ID"),
                                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Industry name")
                            })
                        )
                    }
                )
            ),
            401: openapi.Response(description="Unauthorized - User must be authenticated."),
            403: openapi.Response(description="Forbidden - Only employers and admins can access."),
        }
    )
    @action(detail=False, methods=["get"], url_path="industries-used", permission_classes=[IsAdminAndEmployer])
    def industries_used(self, request):
        """Get the total count and paginated list of industries an employer has posted jobs under."""
        employer = request.user

        industries = Industry.objects.filter(jobs__posted_by=employer).distinct()
        paginator = CustomPagination()
        paginated_industries = paginator.paginate_queryset(industries, request)
        serialized_data = IndustrySerializer(paginated_industries, many=True).data
        return paginator.get_paginated_response(serialized_data)

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
        except Http404:
            return Response({"error": "No Category matches the given query."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class JobViewSet(viewsets.ModelViewSet):
    """API endpoint for jobs with optimized categorized-jobs endpoint."""
    queryset = Job.objects.select_related("industry", "posted_by").only(
        "id", "title", "industry__name", "description", "location", "type", "posted_by__id"
    ).order_by("-posted_at")
    
    serializer_class = JobSerializer
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    permission_classes = [ReadOnlyModifyByAdminEmployer]
    search_fields = ["title", "type", "location", "industry__name"]

    def perform_create(self, serializer):
        """Assign the authenticated user as the poster and clear cache."""
        serializer.save(posted_by=self.request.user)
        cache.delete("job_list")

    def perform_update(self, serializer):
        """Update a job and clear related caches."""
        job = serializer.save()
        cache.delete("job_list")
        cache.delete(f"job_{job.id}")

    def perform_destroy(self, instance):
        """Delete a job and clear related caches."""
        cache.delete("job_list")
        cache.delete(f"job_{instance.id}")
        instance.delete()

    @swagger_auto_schema(
        operation_summary="List Jobs",
        operation_description=(
        "Fetch a paginated list of jobs. All users have access."
        "- User can search jobs by their name. \n\n"
        "- User can set size of data retrieved using page_size and user can navigate to any page using page. \n\n"
        "- **N.B**: There is 2 minutes cache on data retrieved.\n\n"
        "- Both authorized and unauthorized users can access this endpoint."
    ),
        responses={200: JobSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """Cache the job listing response while applying search and pagination."""
        cached_jobs = cache.get("job_list")

        if cached_jobs is None or "search" in request.query_params or "page_size" in request.query_params:
            queryset = self.filter_queryset(self.get_queryset()) 
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                response = self.get_paginated_response(serializer.data)
                cache.set("job_list", response.data, timeout=60 * 2)
                return response
            
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)
            cache.set("job_list", response.data, timeout=60 * 2)
            return response
        
        return Response(cached_jobs)

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
        """Cache individual job details."""
        job_id = kwargs.get("pk")
        cache_key = f"job_{job_id}"
        
        job_data = cache.get(cache_key)
        if job_data is None:
            response = super().retrieve(request, *args, **kwargs)
            cache.set(cache_key, response.data, timeout=60 * 10)
            return response
        
        return Response(job_data)
    
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
    operation_summary="Retrieve categorized jobs by industry, type, or location.",
    operation_description=(
        "Fetch a paginated list of jobs filtered dynamically by industry, type, or location. "
        "Users can specify the category as a query parameter. "
        "Example usage: `/api/job/categorized-jobs/?category=industry`.\n\n"
        "**Available categories:**\n"
        "- `industry`: Groups jobs based on industry.\n"
        "- `type`: Groups jobs based on job type.\n"
        "- `location`: Groups jobs based on job location.\n\n"
        "Both authorized and unauthorized users can access this endpoint."
    ),
    manual_parameters=[
        openapi.Parameter(
            "category",
            openapi.IN_QUERY,
            description="Category to filter jobs by (industry, type, or location). Example: `/api/job/categorized-jobs/?category=industry`.",
            type=openapi.TYPE_STRING,
            enum=["industry", "type", "location"],
            required=True
        ),
        openapi.Parameter(
            "filter",
            openapi.IN_QUERY,
            description="Optional filter to return jobs from a specific category value. Example: `/api/job/categorized-jobs/?category=location&filter=Lagos`.",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            "search",
            openapi.IN_QUERY,
            description="Optional search query to filter jobs by title, industry, location, or type.",
            type=openapi.TYPE_STRING,
            required=False
        )
    ],
    responses={
        200: JobSerializer(many=True),
        400: "Invalid category. Use location, type, or industry.",
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
                Q(type__contains=[search_query])
            )

        category_field = "industry_name" if category == "industry" else category
        jobs = jobs.values("id", "title", "industry_name", "location", "type", "wage").order_by("-posted_at")
        job_groups = defaultdict(list)
        for job in jobs:
            if category == "type":
                for job_type in job["type"]:
                    job_groups[job_type].append(job)
            else:
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
        applicants = Application.objects.filter(job=job).select_related("applicant")
        paginator = CustomPagination()
        paginated_applicants = paginator.paginate_queryset(applicants, request)
        job_data = AppJobSerializer(job).data
        serializer = ApplicationSerializer(paginated_applicants, many=True)
        response_data = {
            "job": job_data,
            "applicants": serializer.data
        }
        return paginator.get_paginated_response(response_data)
    
    @swagger_auto_schema(
        method="get",
        operation_summary="Get distinct job locations",
        operation_description="Returns a paginated list of distinct job locations.",
        manual_parameters=[
            openapi.Parameter(
                name="page",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="Page number for pagination",
            ),
            openapi.Parameter(
                name="page_size",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="Number of locations per page (default: 20, max: 100)",
            ),
        ],
        responses={
            200: openapi.Response(
                description="Paginated list of distinct job locations",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "count": openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
                        "next": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format=openapi.FORMAT_URI,
                            example="http://localhost:8000/api/job/locations/?page=2"
                        ),
                        "previous": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format=openapi.FORMAT_URI,
                            example=None
                        ),
                        "results": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING, example="Lagos"),
                        ),
                    },
                ),
            )
        },
    )
    @action(detail=False, methods=["get"])
    def locations(self, request):
        """Get paginated distinct job locations"""
        search_query = request.GET.get("search", "").strip()
        locations = Job.objects.exclude(location="").values_list("location", flat=True).distinct()
        if search_query:
            locations = [loc for loc in locations if search_query.lower() in loc.lower()]
        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(locations, request)
        return paginator.get_paginated_response(result_page)
    
    @swagger_auto_schema(
        operation_summary="Get total number of jobs posted by the employer/admin",
        operation_description="Returns the total number of jobs posted by the currently signed-in employer/admin.",
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "total_jobs": openapi.Schema(type=openapi.TYPE_INTEGER, example=15)
            }
        )}
    )
    @action(detail=False, methods=["get"], url_path="total-jobs", permission_classes=[IsAdminAndEmployer])
    def total_jobs(self, request):
        """Returns the total number of jobs posted by the signed-in employer/admin"""
        user = request.user
        total_jobs = Job.objects.filter(posted_by=user).count()
        return Response({"total_jobs": total_jobs})

    @swagger_auto_schema(
        operation_summary="Get total applicants for all jobs posted by the employer/admin",
        operation_description="Returns the total number of applicants who have applied to jobs posted by the signed-in employer.",
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "all_applicants": openapi.Schema(type=openapi.TYPE_INTEGER, example=50)
            }
        )}
    )
    @action(detail=False, methods=["get"], url_path="total-applicants", permission_classes=[IsAdminAndEmployer])
    def total_applicants(self, request):
        """Returns the total number of applicants for all jobs posted by the signed-in employer."""
        user = request.user
        
        all_employer_jobs = Job.objects.filter(posted_by=user)
        
        total_applicants = Application.objects.filter(job__in=all_employer_jobs).count()
        
        return Response({"all_applicants": total_applicants})