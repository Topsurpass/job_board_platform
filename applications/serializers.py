from rest_framework import serializers
from .models import Application
from jobs.models import Job
from users.models import User


class AppJobSerializer(serializers.ModelSerializer):
    """Serializer to display job details instead of just the job ID"""
    class Meta:
        model = Job
        exclude = ["industry", "category", "posted_by"]

class ApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","first_name","last_name", "email", "phone"]

class ApplicationBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        exclude = ["status", "applicant"]
class ApplicationSerializer(serializers.ModelSerializer):
    applicant = ApplicantSerializer(read_only=True)
    job = AppJobSerializer(read_only=True)
    class Meta:
        model = Application
        fields = '__all__'
        extra_kwargs = {'applicant': {'read_only': True}}

    def create(self, validated_data):
        request = self.context.get("request")
        job_id = request.data.get("job")

        if not job_id:
            raise serializers.ValidationError({"job": "This field is required."})
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise serializers.ValidationError({"job": "Invalid job ID."})

        validated_data["job"] = job
        return super().create(validated_data)