from rest_framework import routers
from .views import IndustryViewSet, JobViewSet, ApplicationViewSet
from django.urls import path, include


router = routers.DefaultRouter()
router.register(r'industry', IndustryViewSet, basename='industry')
router.register(r'job', JobViewSet, basename='job')
router.register(r'application', ApplicationViewSet, basename='application')


joburlpatterns = [
    path('', include(router.urls)),
]