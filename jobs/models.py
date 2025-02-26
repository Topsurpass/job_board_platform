from django.db import models
import uuid
from users.models import User

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="categories")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


    def __str__(self):
        return self.name

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
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="jobs")
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="jobs")
    posted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.title


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    cover_letter = models.TextField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = ("job", "applicant") 

    def __str__(self):
        return f"{self.applicant.email} applied for {self.job.title}"
