import pytest
from django.urls import reverse
from rest_framework import status
from jobs.models import Industry, Category, Job
from applications.models import Application
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model


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
def auth_client_admin2(api_client, admin2):
    """Authenticates the API client with a test admin"""
    api_client.force_authenticate(user=admin2)
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
def admin2(db):
    """Create test admin"""
    return User.objects.create_user(
        email="admin2@example.com",
        password="securepassword",
        first_name="Admin2",
        last_name="Doe2",
        is_staff="True",
        is_superuser="True",
        role="admin",
        phone="1234567890"
    )

@pytest.fixture
def industry(user):
    """Create a sample industry."""
    return Industry.objects.create(name="Tech", created_by=user)

@pytest.fixture
def category(admin, industry):
    """Create a sample industry."""
    return Category.objects.create(name="Software", industry=industry, created_by=admin)



@pytest.mark.django_db
class TestIndustryViewSet:
    def test_list_industries(self, api_client, user):
        Industry.objects.create(name="Tech", created_by=user)
        Industry.objects.create(name="Finance", created_by=user)
        
        url = reverse("industry-list")
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) > 1

    def test_retrieve_industry(self, api_client, industry):
        url = reverse("industry-detail", args=[industry.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Tech"

    def test_create_industry_by_admin(self, auth_client_admin, admin):
        url = reverse("industry-list")
        data = {"name": "Healthcare", "created_by": admin}
        response = auth_client_admin.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Industry.objects.filter(name="Healthcare").exists()

    def test_create_industry_by_user(self, auth_client_user, user):
        url = reverse("industry-list")
        data = {"name": "Banking", "created_by": user}
        response = auth_client_user.post(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not Industry.objects.filter(name="Banking").exists()

    def test_update_industry_by_user(self, auth_client_user, industry):
        url = reverse("industry-detail", args=[industry.id])
        data = {"name": "Updated Tech"}
        response = auth_client_user.put(url, data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        industry.refresh_from_db()
        assert industry.name != "Updated Tech"

    def test_update_industry_by_admin(self, auth_client_admin, industry):
        url = reverse("industry-detail", args=[industry.id])
        data = {"name": "Updated Tech"}
        response = auth_client_admin.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        industry.refresh_from_db()
        assert industry.name == "Updated Tech"

    def test_partial_update_industry_by_user(self, auth_client_user, industry):
        url = reverse("industry-detail", args=[industry.id])
        data = {"name": "AI & Tech"}
        response = auth_client_user.patch(url, data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        industry.refresh_from_db()
        assert industry.name != "AI & Tech"

    def test_delete_industry_by_user(self, auth_client_user, industry):
        url = reverse("industry-detail", args=[industry.id])
        response = auth_client_user.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Industry.objects.filter(id=industry.id).exists()

    def test_delete_industry_by_admin(self, auth_client_admin, industry):
        url = reverse("industry-detail", args=[industry.id])
        response = auth_client_admin.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Industry.objects.filter(id=industry.id).exists()

    def test_get_industry_jobs(self, api_client, industry, user):
        Job.objects.create(title="Developer", industry=industry, location="Remote", type=["full-time"], posted_by=user)
        
        url = reverse("industry-detail", args=[industry.id]) + "jobs/"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) == 1
        assert response.json()["results"][0]["title"] == "Developer"

    def test_industry_not_found(self, api_client):
        url = reverse("industry-list", args=[999])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
            
    def test_get_categories_by_industry_admin(self, auth_client_admin):      
        url = reverse("industry-list") + "categories-by-industry/"
        response = auth_client_admin.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.json()
        assert len(response.json()["results"]) == 0

    def test_get_categories_by_industry_unauthorized(self, api_client):
        url = reverse("industry-list") + "categories-by-industry/"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_get_industries_used_unauthorized(self, api_client):
        url = reverse("industry-list") + "industries-used/"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_user_get_industries_used_unauthorized(self, auth_client_user):
        url = reverse("industry-list") + "industries-used/"
        response = auth_client_user.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    

@pytest.mark.django_db
class TestCategoryViewSet:
    def test_admin_create_category(self, auth_client_admin, industry, admin):
        url = reverse("category-list")
        data = {"name": "Software",  "created_by": admin, "industry": industry.id}
        response = auth_client_admin.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Category.objects.filter(name="Software").exists()
        
    def test_user_create_category(self, auth_client_user, industry, user):
        url = reverse("category-list")
        data = {"name": "Software", "created_by": user, "industry": industry.id}
        response = auth_client_user.post(url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not Category.objects.filter(name="Software").exists()
        
    def test_get_category_jobs(self, api_client, industry, category, admin):
        Job.objects.create(title="Backend Developer", industry=industry, category=category, location="Remote", type=["full-time"], posted_by=admin)
        
        url = reverse("category-detail", args=[category.id]) + "jobs/"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) == 1
        assert response.json()["results"][0]["title"] == "Backend Developer"

@pytest.mark.django_db
class TestJobViewSet:
    def test_list_jobs(self, api_client, industry, category, admin):
        Job.objects.create(title="Frontend Developer", industry=industry, category=category, location="Remote", type=["full-time"], posted_by=admin)
        Job.objects.create(title="Backend Developer", industry=industry, category=category, location="Remote", type=["part-time"], posted_by=admin)
        
        url = reverse("job-list")
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) > 1

    def test_create_job_by_admin(self, auth_client_admin, admin, industry, category):        
        url = reverse("job-list")
        data = {
            "title": "Software Engineer",
            "industry": industry.id,
            "category": category.id,
            "location": "Remote",
            "responsibilities": "Just come",
            "required_skills": "python",
            "company": "NIBBS",
            "type": ["full-time"],
            "description": "Great job opportunity",
            "posted_by": admin.id
        }
        response = auth_client_admin.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["title"] == "Software Engineer"

    def test_create_job_by_user(self, auth_client_user, admin, industry, category):        
        url = reverse("job-list")
        data = {
            "title": "Software Engineer",
            "industry": industry.id,
            "category": category.id,
            "location": "Remote",
            "company": "NIBBS",
            "type": ["full-time"],
            "description": "Great job opportunity",
            "posted_by": admin.id
        }
        response = auth_client_user.post(url, data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_categorized_jobs(self, api_client, admin, industry, category):
        Job.objects.create(title="Backend Engineer", industry=industry, category=category, location="NY", type=["full-time"],  posted_by=admin)
        Job.objects.create(title="Frontend Engineer", industry=industry, category=category, location="CA", type=["full-time"],  posted_by=admin)
        
        url = reverse("job-list") + "categorized-jobs/?category=location"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert "NY" in response.json()
        assert "CA" in response.json()

    def test_get_job_applicants_by_user(self, api_client, admin, user, industry, category):
        """Get applicants of a job without unauthorized"""
        job = Job.objects.create(title="Data Scientist", industry=industry, category=category, location="Remote", type=["full-time"], posted_by=admin)
        Application.objects.create(job=job, applicant=user)

        url = reverse("job-detail", args=[job.id]) + "applicants/"

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_applicants_by_authenticated_user(self, auth_client_user, admin, user, industry, category):
        job = Job.objects.create(title="Data Scientist", industry=industry, category=category, location="Remote", type=["full-time"], posted_by=admin)
        Application.objects.create(job=job, applicant=user)

        url = reverse("job-detail", args=[job.id]) + "applicants/"

        response = auth_client_user.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_applicants_by_authenticated_admin(self, auth_client_admin, admin, user, industry, category):
        job = Job.objects.create(title="Data Scientist", industry=industry, category=category, location="Remote", type=["full-time"], posted_by=admin)
        Application.objects.create(job=job, applicant=user)

        url = reverse("job-detail", args=[job.id]) + "applicants/"

        response = auth_client_admin.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]["applicants"]) == 1

    def test_total_jobs(self, auth_client_admin, admin, industry, category):
        """Test if an employer gets the correct total number of their posted jobs."""
        Job.objects.create(title="Backend Engineer", industry=industry, category=category, location="NY", type=["full-time"],  posted_by=admin)
        Job.objects.create(title="Frontend Engineer", industry=industry, category=category, location="CA", type=["full-time"],  posted_by=admin)
        url = reverse("job-list") + "total-jobs/"
        
        response = auth_client_admin.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total_jobs"] == 2
        
    def test_user_cannot_access_total_jobs(self, auth_client_user, admin, industry, category):
        """Test user cannot gets the total number of posted jobs as they cant post jobs."""
        Job.objects.create(title="Backend Engineer", industry=industry, category=category, location="NY", type=["full-time"],  posted_by=admin)
        Job.objects.create(title="Frontend Engineer", industry=industry, category=category, location="CA", type=["full-time"],  posted_by=admin)
        url = reverse("job-list") + "total-jobs/"
        
        response = auth_client_user.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
               
    def test_total_jobs_unauthenticated(self, api_client):
        """Test user cannot gets the total number of posted jobs as they cant post jobs."""
        url = reverse("job-list") + "total-jobs/"
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_total_applicants(self, auth_client_admin, admin, user, industry, category):
        """Test if an employer/admin gets the correct total number of applicants on all their posted jobs."""    
        job1 = Job.objects.create(title="Data Scientist", industry=industry, category=category, location="Remote", type=["full-time"], posted_by=admin)
        job2 = Job.objects.create(title="Backend Engineer", industry=industry, category=category, location="NY", type=["full-time"],  posted_by=admin)
        job3 = Job.objects.create(title="Frontend Engineer", industry=industry, category=category, location="CA", type=["full-time"],  posted_by=admin)
        Application.objects.create(job=job1, applicant=user)
        Application.objects.create(job=job2, applicant=user)
        Application.objects.create(job=job3, applicant=user)
        
        url = reverse("job-list") + "total-applicants/"
        
        response = auth_client_admin.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["all_applicants"] == 3   
            
    def test_total_applicants_by_different_job_posters(self, auth_client_admin2, admin,  user, admin2, industry, category):
        """Test if an employer/admin gets the correct total number of applicants on all their posted jobs."""    
        job1 = Job.objects.create(title="Data Scientist", industry=industry, category=category, location="Remote", type=["full-time"], posted_by=admin2)
        job2 = Job.objects.create(title="Backend Engineer", industry=industry, category=category, location="NY", type=["full-time"],  posted_by=admin2)
        job3 = Job.objects.create(title="Frontend Engineer", industry=industry, category=category, location="CA", type=["full-time"],  posted_by=admin)
        Application.objects.create(job=job1, applicant=user)
        Application.objects.create(job=job2, applicant=user)
        Application.objects.create(job=job3, applicant=user)
        
        url = reverse("job-list") + "total-applicants/"
        
        response = auth_client_admin2.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["all_applicants"] == 2
        
    def test_total_applicants_unauthenticated(self, api_client):
        """Test user cannot gets the total number of applicants as they cant post jobs."""
        url = reverse("job-list") + "total-applicants/"
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_user_cannot_access_total_applicants(self, auth_client_user, admin, user, industry, category):
        """Test user cannot gets the total number of applicants for jobs as they cant post jobs."""
        job1 = Job.objects.create(title="Data Scientist", industry=industry, category=category, location="Remote", type=["full-time"], posted_by=admin)
        Application.objects.create(job=job1, applicant=user)

        url = reverse("job-list") + "total-applicants/"
        
        response = auth_client_user.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN