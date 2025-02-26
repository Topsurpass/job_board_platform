from rest_framework import routers
from .views import CategoryViewSet, JobViewSet, ApplicationViewSet
from django.urls import path, include


router = routers.DefaultRouter()
router.register(r'category', CategoryViewSet, basename='category')
router.register(r'job', JobViewSet, basename='job')
router.register(r'application', ApplicationViewSet, basename='application')


joburlpatterns = [
    path('', include(router.urls)),
]