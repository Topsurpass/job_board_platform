from rest_framework import serializers
from .models import UserProfile, User, EmployerProfile
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'role': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        """Dynamically enforce required fields based on role"""
        role = attrs.get('role')

        if role == 'employer':
            if not attrs.get('company_name'):
                raise ValidationError({"company_name": "This field is required for employers."})
            if not attrs.get('industry'):
                raise ValidationError({"industry": "This field is required for users."})
        return attrs

    def create(self, validated_data):
        """Handle user creation with different roles"""
        password = validated_data.pop('password')
        groups = validated_data.pop('groups', [])
        user_permissions = validated_data.pop('user_permissions', [])
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        user.groups.set(groups)
        user.user_permissions.set(user_permissions)
        return user
    
class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the UserProfile model"""
    user = UserSerializer(read_only=True)
    class Meta:
        model = UserProfile
        fields = '__all__'

class EmployerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = EmployerProfile
        fields = '__all__'

class CustomTokenObtainPairSerializer(serializers.Serializer):
    """Serializer for the CustomTokenObtainPairView"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise AuthenticationFailed('Email and password are required.')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed('User with this email does not exist.')

        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect Password')

        attrs['user'] = user
        return attrs
