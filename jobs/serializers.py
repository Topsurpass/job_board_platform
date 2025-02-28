from rest_framework import serializers
from .models import Job, Industry, Category
from applications.models import Application


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = ('id', 'name')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'industry')
        extra_kwargs = {'industry': {'write_only': True}}

class JobSerializer(serializers.ModelSerializer):
    no_of_applicants = serializers.SerializerMethodField()
    class Meta:
        model = Job
        fields = '__all__'
        extra_kwargs = {'industry': {'required' : True}, 'category': {'required': True}, 'posted_by': {'read_only': True}}

    def validate(self, data):
        industry = data.get("industry")
        category = data.get("category")

        if category and industry:
            # Ensure the specified category belongs to the specified industry
            if not Category.objects.filter(id=category.id, industry=industry).exists():
                raise serializers.ValidationError(
                    {"category": f"The {category.name} category does not belong to the specified industry, {industry.name}."}
                )

        return data

    def get_no_of_applicants(self, obj):
        return Application.objects.filter(job=obj).count()