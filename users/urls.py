from django.urls import path
from .views import UserCreateView, UserProfileDetailView, EmployerProfileDetailView

userurlpatterns = [
    path('user/create/', UserCreateView.as_view(), name='user-create'),
    path("user/profile/<uuid:user>/", UserProfileDetailView.as_view(), name="userprofile_detail"),
    path("employer/profile/<uuid:user>/", EmployerProfileDetailView.as_view(), name="employer-profile_detail"),
]

