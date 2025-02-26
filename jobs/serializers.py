from rest_framework import serializers
from .models import Job, Application, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')

class JobSerializer(serializers.ModelSerializer):
    applicants_count = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    class Meta:
        model = Job
        fields = '__all__'

    def get_applicants_count(self, obj):
        return Application.objects.filter(job=obj).count()

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = '__all__'