import uuid
import random
from django.core.management.base import BaseCommand
from jobs.models import Industry
from users.models import User
from django.utils.text import slugify

class Command(BaseCommand):
    help = "Populate the database with job categories."

    def handle(self, *args, **kwargs):
        industry_names = [
        "Information Technology", "Healthcare & Pharmaceuticals", "Financial Services", 
        "Energy & Utilities", "Manufacturing", "Retail & E-commerce", "Telecommunications",
        "Automotive", "Aerospace & Defense", "Real Estate & Construction",
        "Education & Training", "Media & Entertainment", "Hospitality & Tourism",
        "Transportation & Logistics", "Agriculture & Farming", "Consumer Goods",
        "Chemical Industry", "Biotechnology", "Mining & Metals",
        "Legal Services", "Public Administration", "Non-Profit & NGOs",
        "Consulting & Professional Services", "Engineering Services",
        "Insurance", "Food & Beverage", "Fashion & Apparel",
        "Cybersecurity", "Cloud Computing", "Artificial Intelligence & Machine Learning",
        "Game Development", "Blockchain & Cryptocurrency",
        "Renewable Energy", "Oil & Gas", "Textile & Apparel",
        "Publishing & Journalism", "Music & Audio Production",
        "Film & Video Production", "Architecture & Urban Planning",
        "Environmental & Sustainability", "Sports & Recreation",
        "Pharmaceutical Research", "Veterinary Services",
        "Security & Investigation", "Event Management",
        "Advertising & Public Relations"
    ]

        users = list(User.objects.all())

        if not users:
            self.stdout.write(self.style.ERROR("No users found. Create at least one user first."))
            return

        created_count = 0
        for name in industry_names:
            if not Industry.objects.filter(name=name).exists():
                Industry.objects.create(
                    name=name,
                    description=f"This is the {slugify(name)} industry.",
                    created_by=random.choice(users)  # Assign random user
                )
                created_count += 1

        if created_count == 0:
            self.stdout.write(self.style.WARNING("No new categories were created, all already exist."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully created {created_count} industries!"))
