import random
import uuid
from django.core.management.base import BaseCommand
from users.models import User
from jobs.models import Job, Industry


class Command(BaseCommand):
    help = "Seed the Job model with sample data"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Seeding jobs..."))

        job_titles = [
            "Software Engineer", "Data Scientist", "Product Manager", "UI/UX Designer",
            "Backend Developer", "Frontend Developer", "Cloud Engineer", "Cybersecurity Analyst",
            "Marketing Manager", "Sales Executive", "Customer Support", "Business Analyst"
        ]

        companies = ["Google", "Amazon", "Microsoft", "Facebook", "Tesla", "Netflix", "Uber", "Stripe", "Airbnb", "Spotify"]
        locations = ["New York", "San Francisco", "London", "Berlin", "Toronto", "Paris", "Dubai", "Singapore", "Lagos", "Sydney"]
        job_types = ["part-time", "full-time", "contract", "internship"]

        industries = list(Industry.objects.all())
        users = list(User.objects.all())

        if not industries:
            self.stdout.write(self.style.ERROR("No industries found! Please seed industries first."))
            return

        if not users:
            self.stdout.write(self.style.ERROR("No users found! Please create at least one user."))
            return

        Job.objects.all().delete()  # Optional: Clears existing jobs

        for _ in range(50):
            job = Job(
                id=uuid.uuid4(),
                title=random.choice(job_titles),
                company=random.choice(companies),
                location=random.choice(locations),
                type=random.choice(job_types),
                wage=random.randint(30000, 200000),
                description="This is a sample job description.",
                industry=random.choice(industries),
                posted_by=random.choice(users),
                is_active=True,
            )
            job.save()

        self.stdout.write(self.style.SUCCESS("Successfully seeded 50 jobs!"))
