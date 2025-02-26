from .models import User, UserProfile, EmployerProfile
from .serializers import UserSerializer, UserProfileSerializer, EmployerProfileSerializer
from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny
from .tasks.email_tasks import send_welcome_email, send_employer_welcome_email
from rest_framework.response import Response
from rest_framework import status
from users.permissions import IsOwnerBasedOnRole, IsOnlyAdmin

class UserCreateView(generics.CreateAPIView):
    """Create new user account"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        user = serializer.save()

        if user.role == 'user':
            send_welcome_email.delay(user.email, user.first_name)
        elif user.role == 'employer':
            employer_profile = EmployerProfile.objects.filter(user=user).first()
            if employer_profile:
                send_employer_welcome_email.delay(user.email, user.company_name)

        return Response({"message": "Account created successfully. A welcome email has been sent."}, status=status.HTTP_201_CREATED)
    
class UserViewSet(viewsets.ModelViewSet):
    """API for getting all users and modifying their details"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOnlyAdmin]

class UserProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve single user full profile for retrieval, update and deletion"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = "user"
    permission_classes = [IsOwnerBasedOnRole]

class EmployerProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve single user full profile for retrieval, update and deletion"""
    queryset = EmployerProfile.objects.all()
    serializer_class = EmployerProfileSerializer
    lookup_field = "user"
    permission_classes = [IsOwnerBasedOnRole]
