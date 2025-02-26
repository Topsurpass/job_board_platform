from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import uuid

class CustomUserManager(BaseUserManager):
    """Custom manager for User model where email is the unique identifier"""

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password"""
        if not email:
            raise ValueError("The Email field must be set")
        
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with admin permissions"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Custom User model extending Django's AbstractUser"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True, db_index=True) 
    phone = models.CharField(max_length=15, blank=True, null=True)

    ROLE_CHOICES = [
        ('user', 'USER'),
        ('employer', 'EMPLOYER'),
        ('admin', 'ADMIN') 
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user'
    )
    company_name = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    
    password = models.CharField(max_length=128)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()
    
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_groups",
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions",
        blank=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

class UserProfile(models.Model):
    """User profile for job seekers"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_profile")
    bio = models.TextField(blank=True, null=True)
    portfolio_links = models.JSONField(null=True, blank=True)  # Example: {"GitHub": "https://github.com/user"}
    location = models.TextField()
    
    EXPERIENCE_CHOICES = [
        ("entry", "Entry-level"),
        ("mid", "Mid-level"),
        ("senior", "Senior"),
    ]
    
    experience_level = models.CharField(max_length=10, choices=EXPERIENCE_CHOICES, null=True, blank=True)
    social_media_links = models.JSONField(null=True, blank=True)  # Example: {"Twitter": "https://twitter.com/user"}

    def __str__(self):
        return f"User Profile of {self.user.email}"

class EmployerProfile(models.Model):
    """Employer profile for companies"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employer_profile")
    company_website = models.URLField(blank=True, null=True)
    company_description = models.TextField(blank=True, null=True)
    company_location = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Employer Profile of {self.user.email} ({self.user.company_name})"
