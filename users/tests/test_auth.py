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
def create_user(db):
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
def create_user2(db):
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
def create_employer(db):
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
def generate_tokens(create_user):
    """Generate JWT tokens for the test user."""
    refresh = RefreshToken.for_user(create_user)
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh)
    }

# ___________________Test cases_____________________

@pytest.mark.django_db
def test_login_missing_credentials(api_client):
    """Test login fails if email or password is missing."""
    url = "http://localhost:8000/api/auth/login/"
    response = api_client.post(url, {"email": "test@example.com"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_login_wrong_password(api_client, create_user):
    """Test login fails with incorrect password."""
    url = "http://localhost:8000/api/auth/login/"

    response = api_client.post(url, {"email": create_user.email, "password": "wrongpassword"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_user_can_obtain_token(api_client, create_user):
    """Test that a valid user can obtain an access and refresh token."""
    url = reverse("token_obtain_pair")
    payload = {
        "email": create_user.email,
        "password": "securepassword"
    }

    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data
    assert "refresh_token" in response.data
    assert "user" in response.data


@pytest.mark.django_db
def test_invalid_user_cannot_obtain_token(api_client):
    """Test that an invalid user cannot obtain a token."""
    url = reverse("token_obtain_pair")

    payload = {
        "email": "wrong@example.com",
        "password": "wrongpassword"
    }

    response = api_client.post(url, payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_token_refresh_missing_token(api_client):
    """Test that refresh token fails if no token is provided."""
    url = reverse("token_refresh")

    response = api_client.post(url, {})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_token_refresh(api_client, generate_tokens):
    """Test that a valid refresh token returns a new access token."""
    url = reverse("token_refresh")
    payload = {
        "refresh_token": generate_tokens["refresh_token"]
    }

    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data
    assert "refresh_token" in response.data
    assert "user" in response.data

@pytest.mark.django_db
def test_invalid_refresh_token(api_client):
    """Test that an invalid refresh token is rejected."""
    url = reverse("token_refresh")
    payload = {
        "refresh_token": "invalid_token"
    }

    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.data

@pytest.mark.django_db
def test_protected_route_requires_authentication(api_client):
    """Test that a protected route cannot be accessed without authentication."""
    url = "http://localhost:8000/api/user/"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_user_creation(api_client):
    """Test creating a new user."""
    url = reverse("sign_up_new_account")
    payload = {
        "email": "newuser@example.com",
        "password": "securepassword",
        "first_name": "Alice",
        "last_name": "Johnson",
        "role": "user",
        "phone": "5555555555"
    }

    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert "message" in response.data
    assert response.data["message"] == "Account created successfully. A welcome email has been sent."

@pytest.mark.django_db
def test_user_creation_missing_fields(api_client):
    """Test user creation fails when required fields are missing."""
    url = reverse("sign_up_new_account")

    response = api_client.post(url, {})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data
    assert "password" in response.data

@pytest.mark.django_db
def test_duplicate_user_creation(api_client, create_user):
    """Test that creating a user with an existing email fails."""
    url = reverse("sign_up_new_account")
    payload = {
        "email": create_user.email,
        "password": "newpassword",
        "first_name": "Duplicate",
        "last_name": "User",
        "role": "user",
        "phone": "6666666666"
    }

    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data

@pytest.mark.django_db
def test_employer_has_additional_fields(api_client, create_employer):
    """Test that employer users have additional fields in their token."""
    url = reverse("token_obtain_pair")

    payload = {
        "email": create_employer.email,
        "password": "securepassword"
    }

    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data
    assert "refresh_token" in response.data
    assert response.data["user"]["company_name"] == create_employer.company_name
    assert response.data["user"]["industry"] == create_employer.industry

@pytest.mark.django_db
def test_admin_account_cannot_be_created_by_user_or_employer(api_client, create_employer):
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

@pytest.mark.django_db
def test_user_cannot_access_other_users_data(api_client, create_user2, generate_tokens):
    """Test that a user cannot access another user's data."""
    url = reverse("userprofile_detail", args=[create_user2.id])
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {generate_tokens['access_token']}")
    
    response = api_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_user_cannot_access_employer_profile(api_client, create_employer, generate_tokens):
    """Test that a user cannot view employer's profile"""
    url = reverse("userprofile_detail", args=[create_employer.id])
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {generate_tokens['access_token']}")
    
    response = api_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_employer_signup_missing_industry_field(api_client):
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
    
@pytest.mark.django_db
def test_employer_signup_missing_company_name_field(api_client):
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
def test_logout_invalidates_refresh_token(api_client, generate_tokens):
    """Test that logout invalidates the refresh token."""
    url = reverse("logout_user")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {generate_tokens['access_token']}")
    
    response = api_client.post(url, {"refresh_token": generate_tokens["refresh_token"]})
    assert response.status_code == status.HTTP_205_RESET_CONTENT
    
    # Try using the old refresh token
    refresh_url = reverse("token_refresh")
    response = api_client.post(refresh_url, {"refresh_token": generate_tokens["refresh_token"]})
    assert response.status_code == status.HTTP_400_BAD_REQUEST