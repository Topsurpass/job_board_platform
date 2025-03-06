import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from applications.models import Application
from django.contrib.auth import get_user_model
from jobs.models import Industry, Category, Job

pytestmark = pytest.mark.django_db

User = get_user_model()

@pytest.fixture
def api_client():
    """For unauthenticated endpoint"""
    return APIClient()

@pytest.fixture
def auth_client_user(api_client, user):
    """Authenticates the API client with a test user"""
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def auth_client_admin(api_client, admin):
    """Authenticates the API client with a test admin"""
    api_client.force_authenticate(user=admin)
    return api_client

@pytest.fixture
def user(db):
    """Create test user"""
    return User.objects.create_user(
        email="testuser@example.com",
        password="securepassword",
        first_name="John",
        last_name="Doe",
        role="user",
        phone="1234567890"
    )

@pytest.fixture
def admin(db):
    """Create test admin"""
    return User.objects.create_user(
        email="admin@example.com",
        password="securepassword",
        first_name="Admin",
        last_name="Doe",
        is_staff="True",
        is_superuser="True",
        role="admin",
        phone="1234567890"
    )

@pytest.fixture
def industry(admin):
    """Create a sample industry."""
    return Industry.objects.create(name="Tech", created_by=admin)

@pytest.fixture
def category(admin, industry):
    """Create a sample industry."""
    return Category.objects.create(name="Software", industry=industry, created_by=admin)

@pytest.fixture
def job(industry, admin):
    return Job.objects.create(title="Developer", industry=industry, location="Remote", type=["full-time"], posted_by=admin)

@pytest.fixture
def application(user, job):
    """Creates a sample job application"""
    return Application.objects.create(
        applicant=user,
        job=job,
        resume_link="https://example.com/resume.pdf",
        cover_letter="I am excited to apply!"
    )


@pytest.mark.django_db
class TestApplicationViewSet:
    """Tests for the Application API endpoints."""

    def test_create_application(self, auth_client_user, job, user):
        """Test that a user can successfully create an application."""
        data = {
            "job": str(job.id),
            "resume_link": "https://example.com/resume.pdf",
            "cover_letter": "I am excited to apply!"
        }
        url = reverse("application-list")
        response = auth_client_user.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Application.objects.filter(job=job, applicant=user).exists()

    def test_create_application_with_missing_fields(self, auth_client_user, job):
        """Test application creation with missing required fields should fail."""
        data = {"job": str(job.id)}
        url = reverse("application-list")
        response = auth_client_user.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "resume_link" in response.json()
        assert "cover_letter" in response.json()

    def test_create_application_with_invalid_resume_link(self, auth_client_user, job):
        """Test that an application with an invalid resume link is rejected."""
        data = {
            "job": str(job.id),
            "resume_link": "invalid-url",
            "cover_letter": "This should fail due to an invalid URL."
        }
        url = reverse("application-list")
        response = auth_client_user.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "resume_link" in response.json()

    def test_list_applications(self, auth_client_user, application):
        """Test that a user can retrieve their job applications."""
        url = reverse("application-list")
        response = auth_client_user.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) > 0
        assert response.json()["results"][0]["cover_letter"] == application.cover_letter

    def test_retrieve_application(self, auth_client_user, application):
        """Test that a user can retrieve a specific application."""
        url = reverse("application-detail", args=[application.id])
        response = auth_client_user.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == str(application.id)

    def test_retrieve_non_existent_application(self, auth_client_user):
        """Test retrieving a non-existent application returns 404."""
        url = reverse("application-detail", args=['897hd7hs'])
        response = auth_client_user.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_cannot_apply_twice(self, auth_client_user, job):
        """Test that a user cannot apply for the same job twice."""
        data = {
            "job": str(job.id),
            "resume_link": "https://example.com/resume.pdf",
            "cover_letter": "First application"
        }
        url = reverse("application-list")
        auth_client_user.post(url, data)
        
        response = auth_client_user.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.json()

    def test_unauthenticated_user_cannot_apply(self, api_client, job):
        """Test that an unauthenticated user cannot create an application."""
        data = {
            "job": str(job.id),
            "resume_link": "https://example.com/resume.pdf",
            "cover_letter": "This should not be allowed."
        }
        response = api_client.post("/api/application/", data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAdminApplicationActions:
    """Tests for admin actions on applications."""

    def test_admin_can_update_application_status(self, auth_client_admin, application):
        """Test that an admin can update the status of an application."""
        data = {"status": "accepted"}
        url = reverse("application-detail", args=[application.id])
        response = auth_client_admin.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        application.refresh_from_db()
        assert application.status == "accepted"

    def test_admin_cannot_set_invalid_status(self, auth_client_admin, application):
        """Test that an admin cannot set an invalid application status."""
        data = {"status": "invalid_status"}
        url = reverse("application-detail", args=[application.id])
        response = auth_client_admin.patch(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in response.json()

    def test_admin_can_delete_application(self, auth_client_admin, application):
        """Test that an admin can delete an application."""
        url = reverse("application-detail", args=[application.id])
        response = auth_client_admin.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Application.objects.filter(id=application.id).exists()

    def test_non_admin_cannot_delete_application(self, auth_client_user, application):
        """Test that a normal user cannot delete an application they did not create."""
        url = reverse("application-detail", args=[application.id])
        response = auth_client_user.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_can_delete_own_application(self, auth_client_user, application):
        """Test that a user can delete their own application."""
        url = reverse("application-detail", args=[application.id])
        response = auth_client_user.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_user_cannot_delete_application(self, api_client, application):
        """Test that an unauthenticated user cannot delete any applications."""
        url = reverse("application-detail", args=[application.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_user_cannot_access_application_list(self, api_client):
        """Test that an unauthenticated user cannot access the application list."""
        url = reverse("application-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
