from django.db import models
import uuid
from users.models import User
from jobs.models import Job


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    resume_link = models.URLField(max_length=255, blank=True, null=True)
    cover_letter = models.TextField(blank=True, null=True)

    STATUS_STATE = [
        ("pending", "Pending"),
        ("submitted", "Submitted"),
        ("reviewed", "Reviewed"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]
    
    status = models.CharField(max_length=10, choices=STATUS_STATE, default='pending', db_index=True)
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["job", "applicant"], name="unique_application")
        ] 

    def __str__(self):
        return f"{self.applicant.email} applied for {self.job.title}"