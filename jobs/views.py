import traceback
from django.conf import settings
from rest_framework import viewsets, filters, serializers, status
from .models import Job, Industry, Category
from django.db.models import Count
from applications.models import Application
from applications.serializers import ApplicationSerializer, AppJobSerializer
from .serializers import IndustrySerializer, JobSerializer, CategorySerializer, CategoryIndustrySerializer, JobListSerializer
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
from django.core.exceptions import ValidationError


logger = logging.getLogger(__name__)

class IndustryViewSet(viewsets.ModelViewSet):
    """API endpoint for performing CRUD functions on industries with paginated jobs."""
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
        
        industry = self.get_object()
        
        jobs = Job.objects.filter(industry=industry).select_related("posted_by", "category").order_by("-posted_at")
        
        if not jobs.exists():
            return Response({"message": "No jobs found in this industry."}, status=status.HTTP_404_NOT_FOUND)

        paginator = CustomPagination()
        paginated_jobs = paginator.paginate_queryset(jobs, request)
        
        serializer = JobSerializer(paginated_jobs, many=True)
        
        return paginator.get_paginated_response(serializer.data)

    
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

        industry = self.get_object()
        
        categories = Category.objects.filter(industry=industry).select_related("industry").order_by("-created_at")
        
        if not categories.exists():
            return Response({"message": "No categories found for this industry."}, status=status.HTTP_200_OK)

        paginator = CustomPagination()
        paginated_categories = paginator.paginate_queryset(categories, request)
        
        serializer = CategorySerializer(paginated_categories, many=True)
        
        return paginator.get_paginated_response(serializer.data)
    
    
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
        if not all_industries.exists():
            return Response({"message": "No industries available."}, status=status.HTTP_200_OK)
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
        cache_key = f"industries_used_{employer.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        industries = Industry.objects.filter(jobs__posted_by=employer).distinct()
        paginator = CustomPagination()
        paginated_industries = paginator.paginate_queryset(industries, request)
        serialized_data = IndustrySerializer(paginated_industries, many=True).data
        response =  paginator.get_paginated_response(serialized_data)
        cache.set(cache_key, response.data, timeout=120)

        return response

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
            jobs = Job.objects.filter(category=category).select_related("category").order_by('-posted_at')

            paginator = CustomPagination()
            paginated_jobs = paginator.paginate_queryset(jobs, request, view=self)
            serializer = JobSerializer(paginated_jobs, many=True)

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            logger.error(f"Unexpected error in get_category_jobs: {str(e)}\n{traceback.format_exc()}")
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        self.clear_cache()

    def perform_update(self, serializer):
        """Update a job and clear related caches."""
        instance = serializer.save()
        self.clear_cache()
        cache.delete(f"job_{instance.id}")

    def perform_destroy(self, instance):
        """Delete a job and clear related caches."""
        self.clear_cache()
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
        """Fetch job listings, ensure absolute picture URLs, and apply caching."""

        cache_key = f"job_list_{request.query_params.get('search', '')}_{request.query_params.get('page', '')}_{request.query_params.get('page_size', '')}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        def get_absolute_picture_url(picture_url):
            """Return absolute URL for job picture based on environment."""
            if not picture_url:
                return None

            if settings.DEBUG:
                return request.build_absolute_uri(picture_url) if request else picture_url
            else:
                if not picture_url.startswith("http"):
                    cloud_name = getattr(settings, "CLOUDINARY_CLOUD_NAME", "temz-cloudinary")
                    return f"https://res.cloudinary.com/{cloud_name}/{picture_url}"
                return picture_url

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = JobListSerializer(page, many=True, context={"request": request})
            response = self.get_paginated_response(serializer.data)
        else:
            serializer = JobListSerializer(queryset, many=True, context={"request": request})
            response = Response(serializer.data)

        for job in response.data["results"]:
            if "picture" in job:
                job["picture"] = get_absolute_picture_url(job["picture"]) 
    
        cache.set(cache_key, response.data, timeout=120) 
        return response
    
    def clear_cache(self):
        """Clear all job-related cache keys."""
        cache.delete_pattern("job_list_*")
    
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
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Retrieve a job",
        operation_description="Get detailed information about a specific job.",
        responses={200: JobSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        """Fetch individual job details, ensure absolute picture URL, and apply caching."""

        job_id = kwargs.get("pk")
        cache_key = f"job_{job_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        def get_absolute_picture_url(picture_url):
            """Return absolute URL for job picture based on environment."""
            if not picture_url:
                return None

            if settings.DEBUG:
                return request.build_absolute_uri(picture_url) if request else picture_url
            else:
                if not picture_url.startswith("http"):
                    cloud_name = getattr(settings, "CLOUDINARY_CLOUD_NAME", "temz-cloudinary")
                    return f"https://res.cloudinary.com/{cloud_name}/{picture_url}"
                return picture_url

        response = super().retrieve(request, *args, **kwargs)
        job_data = response.data

        if "picture" in job_data:
            job_data["picture"] = get_absolute_picture_url(job_data["picture"])

        cache.set(cache_key, job_data, timeout=120)
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

        jobs = Job.objects.annotate(industry_name=F("industry__name"), category_name=F("category__name"), no_of_applicants=Count("applications"))
        if search_query:
            jobs = jobs.filter(
                Q(title__icontains=search_query) |
                Q(industry__name__icontains=search_query) |
                Q(location__icontains=search_query) |
                Q(type__icontains=[search_query])
            )

        category_field = "industry_name" if category == "industry" else category
        jobs = jobs.values(
            "id", "title", "industry_name", "category_name",
            "location", "required_skills", "type", "wage",
            "description", "no_of_applicants", "is_active"
            ).order_by("-posted_at")
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
        def generate_locations():
            for location in Job.objects.exclude(location="").values_list("location", flat=True).distinct():
                if not search_query or search_query.lower() in location.lower():
                    yield location

        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(list(generate_locations()), request)
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
        operation_summary="List all jobs posted by signed-in employer/admin",
        operation_description="Returns the paginated list of jobs posted by the currently signed-in employer/admin.",
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "total_jobs": openapi.Schema(type=openapi.TYPE_INTEGER, example=15)
            }
        )}
    )
    @action(detail=False, methods=["get"], url_path="list-total-jobs", permission_classes=[IsAdminAndEmployer])
    def list_total_jobs(self, request):
        """Returns the list of total number of jobs posted by the signed-in employer/admin"""
        user = request.user
        def generate_jobs():
            for job in Job.objects.filter(posted_by=user):
                yield job

        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(list(generate_jobs()), request)
        serializer = JobListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

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
        
    @swagger_auto_schema(
        method="get",
        operation_summary="Get total applicants for jobs posted by the employer.",
        operation_description=(
            "This endpoint returns a list of job applications categorized by jobs posted by the signed-in employer.\n\n"
            "**Response Structure:**\n"
            "- `total_applications`: Total number of applicants across all jobs.\n"
            "- `all_applications`: List of jobs with the number of applicants and detailed application data.\n\n"
        ),
        responses={
            200: openapi.Response(
                description="List of jobs with categorized applications.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "total_applications": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total number of applicants across all jobs."),
                        "all_applications": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "job_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the job."),
                                    "job_title": openapi.Schema(type=openapi.TYPE_STRING, description="Title of the job."),
                                    "no_of_applicants": openapi.Schema(type=openapi.TYPE_INTEGER, description="Number of applicants for the job."),
                                    "applications": openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Application ID."),
                                                "applicant_name": openapi.Schema(type=openapi.TYPE_STRING, description="Name of the applicant."),
                                                "status": openapi.Schema(type=openapi.TYPE_STRING, description="Status of the application."),
                                                "resume_url": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description="URL of the applicant's resume.")
                                            }
                                        )
                                    )
                                }
                            )
                        )
                    }
                )
            ),
            403: openapi.Response(
                description="Forbidden. Only employers and admins can access this endpoint."
            ),
        }
    )
    @action(detail=False, methods=["get"], url_path="list-total-applicants", permission_classes=[IsAdminAndEmployer])
    def list_total_applicants(self, request):
        """Returns categorized applications for jobs posted by the signed-in employer, using yield for better memory efficiency."""
        user = request.user

        def generate_categorized_applications():
            for job in Job.objects.filter(posted_by=user):
                job_applications = Application.objects.filter(job=job)
                if job_applications.exists():
                    yield {
                        "job_id": job.id,
                        "job_title": job.title,
                        "no_of_applicants": job_applications.count(),
                        "applications": ApplicationSerializer(job_applications, many=True).data
                    }

        paginator = CustomPagination()
        paginated_result = paginator.paginate_queryset(list(generate_categorized_applications()), request)

        response_data = {
            "total_applications": sum(job["no_of_applicants"] for job in paginated_result),
            "all_applications": paginated_result
        }

        return paginator.get_paginated_response(response_data)