from rest_framework import serializers
from .models import Job, Industry, Category
from applications.models import Application
import json


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = ('id', 'name')

class CategorySerializer(serializers.ModelSerializer):
    industry = IndustrySerializer()
    class Meta:
        model = Category
        fields = ('id', 'name', 'industry')

class JobSerializer(serializers.ModelSerializer):
    no_of_applicants = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = '__all__'
        extra_kwargs = {
            'industry': {'required': True},
            'category': {'required': True},
            'posted_by': {'read_only': True},
            'responsibilities': {'required': False},
            'required_skills': {'required': False},
            'type': {'required': False},
            'picture': {'required': False, 'allow_null': True},
        }

    def validate(self, data):
        industry = data.get("industry")
        category = data.get("category")

        if category and industry:
            if not Category.objects.filter(id=category.id, industry=industry).exists():
                raise serializers.ValidationError(
                    {"category": f"The {category.name} category does not belong to the specified industry, {industry.name}."}
                )

        job_type = data.get("type", [])
        if isinstance(job_type, str):
            try:
                job_type = json.loads(job_type)
            except json.JSONDecodeError:
                raise serializers.ValidationError({"type": "Invalid JSON format. Must be an array of strings."})

        if not isinstance(job_type, list) or not all(isinstance(t, str) for t in job_type):
            raise serializers.ValidationError({"type": "Job type must be a list of strings."})

        data["type"] = job_type  # Ensure it's always a list

        return data

    def get_no_of_applicants(self, obj):
        return Application.objects.filter(job=obj).count()

    def to_representation(self, instance):
        """Ensure JSON fields (responsibilities, required_skills, and type) return lists."""
        data = super().to_representation(instance)
        data["responsibilities"] = data["responsibilities"] or []
        data["required_skills"] = data["required_skills"] or []
        data["type"] = data["type"] or []
        request = self.context.get('request')
        if instance.picture:
            if instance.picture.url.startswith("http"):  # Already a full URL
                data["picture"] = instance.picture.url
            else:
                data["picture"] = f"https://res.cloudinary.com/temz-cloudinary/{instance.picture.url}"

        return data