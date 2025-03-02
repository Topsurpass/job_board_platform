from django.urls import path, include
from rest_framework import routers
from .views import (
    UserProfileDetailView,
    EmployerProfileDetailView,
    UserViewSet
)

router = routers.DefaultRouter()
router.register(r"user", UserViewSet, basename="user")

userurlpatterns = [
    path("", include(router.urls)),
    path("user/profile/<uuid:user>/", UserProfileDetailView.as_view(), name="userprofile_detail"),
    path("employer/profile/<uuid:user>/", EmployerProfileDetailView.as_view(), name="employer-profile_detail"),
]

