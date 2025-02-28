from rest_framework import routers
from .views import IndustryViewSet, JobViewSet, CategoryViewSet
from django.urls import path, include


router = routers.DefaultRouter()
router.register(r'industry', IndustryViewSet, basename='industry')
router.register(r'job', JobViewSet, basename='job')
router.register(r'category', CategoryViewSet, basename='category')


joburlpatterns = [
    path('', include(router.urls)),
]