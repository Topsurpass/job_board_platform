from rest_framework import viewsets, filters
from .models import Application
from .serializers import ApplicationSerializer
from jobs.permissions import ReadCreateOnlyAdminModify
from jobs.pagination import CustomPagination
# from rest_framework.permissions import AllowAny

class ApplicationViewSet(viewsets.ModelViewSet):
    """API endpoint that allows user to submit application"""
    queryset = Application.objects.all().order_by('-applied_at')
    serializer_class = ApplicationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['job__title', 'job__company', 'job__industry__name', 'status']
    permission_classes = [ReadCreateOnlyAdminModify]
    # permission_classes = [AllowAny]
    pagination_class = CustomPagination

