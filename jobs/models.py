from django.db import models
import uuid
from users.models import User
from django.core.exceptions import ValidationError

class Industry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="categories")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    class Meta:
            verbose_name_plural = "Industries"

    def __str__(self):
        return self.name


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE, related_name="industries")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="industries")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.name} ({self.industry.name})"

class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=255, db_index=True)
    company = models.CharField(max_length=255, db_index=True)
    location = models.CharField(max_length=255, db_index=True)
    wage = models.IntegerField(null=True, blank=True)

    JOB_TYPE_CHOICES = [
        ('part-time', 'PART-TIME'),
        ('full-time', 'FULL-TIME'),
        ('contract', 'CONTRACT'),
        ('internship', 'INTERNSHIP'),
    ]
    
    type = models.CharField(
        max_length=10,
        choices=JOB_TYPE_CHOICES,
        default='full-time',
    )

    EXPERIENCE_CHOICES = [
        ("entry", "Entry-level"),
        ("mid", "Mid-level"),
        ("senior", "Senior"),
    ]
    
    experience_level = models.CharField(max_length=10, choices=EXPERIENCE_CHOICES, null=True, blank=True)
    description = models.TextField()
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, related_name="jobs")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="jobs")
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="jobs")
    posted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.title
    
    def clean(self):
        """Ensure the selected category belongs to the specified industry when using DRF
            and ADMIN page for job creation.
        """
        if self.category and self.industry:
            if self.category.industry != self.industry:
                raise ValidationError({'category': "The selected category does not belong to the specified industry."})

    def save(self, *args, **kwargs):
        """Run clean method before saving the object."""
        self.clean()
        super().save(*args, **kwargs)