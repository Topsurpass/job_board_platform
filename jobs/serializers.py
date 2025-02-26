from rest_framework import serializers
from .models import Job, Application, Industry


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = ('id', 'name')

class JobSerializer(serializers.ModelSerializer):
    no_of_applicants = serializers.SerializerMethodField()
    industry = IndustrySerializer(read_only=True)
    class Meta:
        model = Job
        fields = '__all__'

    def get_no_of_applicants(self, obj):
        return Application.objects.filter(job=obj).count()

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = '__all__'