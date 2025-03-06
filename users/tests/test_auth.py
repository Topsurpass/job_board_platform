import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    """Fixture to create a test user."""
    return User.objects.create_user(
        email="testuser@example.com",
        password="securepassword",
        first_name="John",
        last_name="Doe",
        role="user",
        phone="1234567890"
    )

@pytest.fixture
def user2(db):
    """Fixture to create a test second user."""
    return User.objects.create_user(
        email="testuser2@example.com",
        password="securepassword2",
        first_name="Frank",
        last_name="Mark",
        role="user",
        phone="1234567890"
    )

@pytest.fixture
def employer(db):
    """Fixture to create a test employer."""
    return User.objects.create_user(
        email="employer@example.com",
        password="securepassword",
        first_name="Jane",
        last_name="Smith",
        role="employer",
        phone="0987654321",
        company_name="TechCorp",
        industry="IT"
    )

@pytest.fixture
def generate_tokens(user):
    """Generate JWT tokens for the test user."""
    refresh = RefreshToken.for_user(user)
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh)
    }

@pytest.mark.django_db
class TestAuthentication:
    
    def test_login_missing_credentials(self, api_client):
        url = reverse("token_obtain_pair")
        response = api_client.post(url, {"email": "test@example.com"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_wrong_password(self, api_client, user):
        url = reverse("token_obtain_pair")
        response = api_client.post(url, {"email": user.email, "password": "wrongpassword"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_can_obtain_token(self, api_client, user):
        url = reverse("token_obtain_pair")
        payload = {"email": user.email, "password": "securepassword"}
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert "refresh_token" in response.data
        assert "user" in response.data
    
    def test_invalid_user_cannot_obtain_token(self, api_client):
        url = reverse("token_obtain_pair")
        payload = {"email": "wrong@example.com", "password": "wrongpassword"}
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
@pytest.mark.django_db
class TestToken:
    
    def test_token_refresh_missing_token(self, api_client):
        url = reverse("token_refresh")
        response = api_client.post(url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_token_refresh(self, api_client, generate_tokens):
        url = reverse("token_refresh")
        payload = {"refresh_token": generate_tokens["refresh_token"]}
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
    
    def test_invalid_refresh_token(self, api_client):
        url = reverse("token_refresh")
        payload = {"refresh_token": "invalid_token"}
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_logout_invalidates_refresh_token(self, api_client, generate_tokens):
        url = reverse("logout_user")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {generate_tokens['access_token']}")
        response = api_client.post(url, {"refresh_token": generate_tokens["refresh_token"]})
        assert response.status_code == status.HTTP_205_RESET_CONTENT
        refresh_url = reverse("token_refresh")
        response = api_client.post(refresh_url, {"refresh_token": generate_tokens["refresh_token"]})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestUserManagement:
    
    def test_user_creation(self, api_client):
        url = reverse("sign_up_new_account")
        payload = {"email": "newuser@example.com", "password": "securepassword", "first_name": "Alice", "last_name": "Johnson", "role": "user", "phone": "5555555555"}
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_user_creation_missing_fields(self, api_client):
        """Test user creation fails when required fields are missing."""
        url = reverse("sign_up_new_account")

        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data
        assert "password" in response.data
    
    def test_duplicate_user_creation(self, api_client, user):
        url = reverse("sign_up_new_account")
        payload = {"email": user.email, "password": "newpassword", "first_name": "Duplicate", "last_name": "User", "role": "user", "phone": "6666666666"}
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_employer_has_additional_fields(self, api_client, employer):
        """Test that employer users have additional fields in their token."""
        url = reverse("token_obtain_pair")

        payload = {
            "email": employer.email,
            "password": "securepassword"
        }

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert "refresh_token" in response.data
        assert response.data["user"]["company_name"] == employer.company_name
        assert response.data["user"]["industry"] == employer.industry

    def test_admin_account_cannot_be_created_by_user_or_employer(self, api_client):
        """Test that admin account cannot be created by user or an employer"""
        url = reverse("sign_up_new_account")

        payload = {
            "email":"admin@gmail.com",
            "password": "newpassword",
            "first_name": "Duplicate",
            "last_name": "User",
            "role": "admin",
            "phone": "6666666666"
        }

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_employer_signup_missing_industry_field(self, api_client):
        """Test employer signup fails if required industry field is missing."""
        url = reverse("sign_up_new_account")
        payload = {
            "email": "employer@example.com",
            "password": "securepassword",
            "role": "employer",
            "company_name": "is Lord Enterprise"
        }
        
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "industry" in response.data
        
    def test_employer_signup_missing_company_name_field(self, api_client):
        """Test employer signup fails if required company_name field is missing."""
        url = reverse("sign_up_new_account")
        payload = {
            "email": "employer@example.com",
            "password": "securepassword",
            "role": "employer",
            "industry": "Tech"
        }
        
        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "company_name" in response.data

@pytest.mark.django_db
class TestAccessControl:
    
    def test_protected_route_requires_authentication(self, api_client):
        url = reverse("user-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_cannot_access_other_users_data(self, api_client, user2, generate_tokens):
        url = reverse("userprofile_detail", args=[user2.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {generate_tokens['access_token']}")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_cannot_access_employer_profile(self, api_client, employer, generate_tokens):
        url = reverse("userprofile_detail", args=[employer.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {generate_tokens['access_token']}")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
