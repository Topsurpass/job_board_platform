from rest_framework import viewsets, filters, status
from .models import Job, Industry, Application
from .serializers import IndustrySerializer, JobSerializer, ApplicationSerializer
from .permissions import ReadOnlyForAllUsersModifyByAdmin, ReadCreateOnlyAdminModify
from .pagination import CustomPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from collections import defaultdict
from django.core.paginator import Paginator
from django.db.models import F



logger = logging.getLogger(__name__)

class IndustryViewSet(viewsets.ModelViewSet):
    """API endpoint for industries with paginated jobs."""
    queryset = Industry.objects.all().order_by('-created_at')
    serializer_class = IndustrySerializer
    permission_classes = [ReadOnlyForAllUsersModifyByAdmin]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

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


class JobViewSet(viewsets.ModelViewSet):
    """API endpoint for jobs with optimized categorized-jobs endpoint."""
    
    queryset = Job.objects.select_related("industry", "posted_by").only(
        "id", "title", "industry__name", "location", "type", "posted_by__id"
    ).order_by("-posted_at")
    
    serializer_class = JobSerializer
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    permission_classes = [ReadOnlyForAllUsersModifyByAdmin]
    search_fields = ["title", "type", "location", "industry__name"]

    @swagger_auto_schema(
        operation_summary="Get Job Categories by Industry, location and type",
        operation_description=(
            "This endpoint retrieves all jobs categorized by their Industry, location and type, "
            "with pagination for each category."
        ),
        manual_parameters=[
            openapi.Parameter("page_size", openapi.IN_QUERY, description="Number of jobs per page (default: 10)", type=openapi.TYPE_INTEGER),
            openapi.Parameter("industry_page", openapi.IN_QUERY, description="Page number for industry category", type=openapi.TYPE_INTEGER),
            openapi.Parameter("location_page", openapi.IN_QUERY, description="Page number for 'location' category", type=openapi.TYPE_INTEGER),
            openapi.Parameter("type_page", openapi.IN_QUERY, description="Page number for 'type' category", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response(
                description="Successfully retrieved categorized jobs",
                examples={
                    "application/json": {
                        "industry": {
                            "Publishing & Journalism": {
                                "total_count": 2,
                                "jobs": [
                                    {"id": "28c3add8-2769-43a0-9d10-2468caaec68c", "title": "Business Analyst", "location": "Sydney", "type": "internship", "wage": 170143, "industry_name": "Publishing & Journalism"}
                                ],
                                "pagination": {
                                    "next": "http://localhost:8000/api/job/categorized-jobs/?industry_page=2&page_size=1",
                                    "previous": 'null'
                                }
                            },
                        },
                        "location": {
                            "Sydney": {
                                "total_count": 6,
                                "jobs": [
                                    {"id": "28c3add8-2769-43a0-9d10-2468caaec68c","title": "Business Analyst","industry__name": "Publishing & Journalism", "location": "Sydney", "type": "internship", "wage": 170143, "industry_name": "Publishing & Journalism" }
                                ],
                                "pagination": {
                                    "next": "http://localhost:8000/api/job/categorized-jobs/?industry_page=1&page_size=1&location_page=2",
                                    "previous": 'null'
                                }
                            },
                        },
                        "type": {
                            "contract": {
                                "total_count": 4,
                                "jobs": [
                                    {"id": "28c3add8-2769-43a0-9d10-2468caaec68c","title": "Business Analyst","industry__name": "Publishing & Journalism", "location": "Sydney", "type": "internship", "wage": 170143, "industry_name": "Publishing & Journalism" }
                                ],
                                "pagination": {
                                    "next": "http://localhost:8000/api/job/categorized-jobs/?industry_page=1&page_size=1&location_page=2",
                                    "previous": 'null'
                                }
                            },
                        }
                    }
                },
            ),
            400: openapi.Response("Invalid request parameters"),
            500: openapi.Response("Server error"),
        },
    )


    @action(detail=False, methods=["get"], url_path="categorized-jobs")
    def get_categorized_jobs(self, request):
        """Optimized endpoint to get jobs categorized by industry, location, and type."""

        jobs = (
        Job.objects
        .annotate(industry_name=F("industry__name"))
        .values("id", "title", "industry_name", "location", "type", "wage")
        .order_by("posted_at")
    )
        job_groups = {
            "industry": defaultdict(list),
            "location": defaultdict(list),
            "type": defaultdict(list),
        }
        for job in jobs:
            job_groups["industry"][job["industry_name"] or "Other"].append(job)
            job_groups["location"][job["location"] or "Other"].append(job)
            job_groups["type"][job["type"] or "Other"].append(job)

        paginated_categories = {}
        for category, groups in job_groups.items():
            paginated_categories[category] = {
                key: self._paginate_queryset(request, job_list, category)
                for key, job_list in groups.items()
            }

        return Response(paginated_categories, status=status.HTTP_200_OK)

    def _paginate_queryset(self, request, job_list, category):
        """Helper method to paginate a list of jobs."""
        page_size = int(request.GET.get("page_size", 10))
        page_number = int(request.GET.get(f"{category}_page", 1))
        paginator = Paginator(job_list, page_size)
        page = paginator.get_page(page_number)
        base_url = request.build_absolute_uri().split("?")[0]
        query_params = request.GET.dict()

        query_params[f"{category}_page"] = page.next_page_number() if page.has_next() else None
        next_url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items() if v is not None)}"
        query_params[f"{category}_page"] = page.previous_page_number() if page.has_previous() else None
        prev_url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items() if v is not None)}"

        return {
            "total_count": paginator.count,
            "jobs": list(page),
            "pagination": {
                "next": next_url if page.has_next() else None,
                "previous": prev_url if page.has_previous() else None,
            },
        }


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
class ApplicationViewSet(viewsets.ModelViewSet):
    """API endpoint that allows user to submit application"""
    queryset = Application.objects.all().order_by('-applied_at')
    serializer_class = ApplicationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['job__title', 'job__company', 'job__industry__name']
    permission_classes = [ReadCreateOnlyAdminModify]
    pagination_class = CustomPagination
