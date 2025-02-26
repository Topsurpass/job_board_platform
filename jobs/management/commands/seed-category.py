import uuid
import random
from django.core.management.base import BaseCommand
from jobs.models import Category
from users.models import User
from django.utils.text import slugify

class Command(BaseCommand):
    help = "Populate the database with job categories."

    def handle(self, *args, **kwargs):
        category_names = [
            "Software Engineering", "Data Science", "Cybersecurity", "Cloud Computing", 
            "Product Management", "Marketing", "Sales", "UI/UX Design", "Graphic Design",
            "Human Resources", "Finance", "Accounting", "Business Analysis", "Consulting",
            "Healthcare", "Nursing", "Legal", "Education", "Research & Development",
            "Engineering", "Civil Engineering", "Mechanical Engineering", "Electrical Engineering",
            "Architecture", "Construction", "Real Estate", "Hospitality", "Tourism", 
            "Customer Support", "Operations Management", "Project Management", 
            "Content Writing", "Copywriting", "Social Media Management", "SEO", 
            "E-commerce", "Retail", "Automotive", "Manufacturing", "Logistics & Supply Chain",
            "Public Relations", "Event Management", "Journalism", "Editing & Proofreading",
            "Game Development", "AI & Machine Learning", "Blockchain", "Virtual Reality", 
            "Photography", "Video Production", "Music & Audio Production"
        ]

        users = list(User.objects.all())

        if not users:
            self.stdout.write(self.style.ERROR("No users found. Create at least one user first."))
            return

        created_count = 0
        for name in category_names:
            if not Category.objects.filter(name=name).exists():
                category = Category.objects.create(
                    name=name,
                    description=f"This is the {slugify(name)} category.",
                    created_by=random.choice(users)  # Assign random user
                )
                # self.stdout.write(self.style.SUCCESS(f"Created category: {category.name}"))
                created_count += 1

        if created_count == 0:
            self.stdout.write(self.style.WARNING("No new categories were created, all already exist."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully created {created_count} categories!"))
