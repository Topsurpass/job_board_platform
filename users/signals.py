from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import User, UserProfile, EmployerProfile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'employer':
            EmployerProfile.objects.get_or_create(user=instance)
        else:
            UserProfile.objects.get_or_create(user=instance)
