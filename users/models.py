from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
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


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model extending Django's AbstractBaseUser (no username field)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)

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
    company_name = models.CharField(max_length=255, blank=True, null=True, unique=True)
    industry = models.CharField(max_length=100, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        """Ensure password is hashed when saving via Django Admin"""
        if self.pk:
            stored_user = User.objects.filter(pk=self.pk).first()
            if stored_user and stored_user.password != self.password:
                self.set_password(self.password)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email}"

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
