from rest_framework import routers
from .views import ApplicationViewSet
from django.urls import path, include


router = routers.DefaultRouter()
router.register(r'application', ApplicationViewSet, basename='application')


applicationurlpatterns = [
    path('', include(router.urls)),
]