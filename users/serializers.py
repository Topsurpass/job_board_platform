from rest_framework import serializers
from .models import UserProfile, User, EmployerProfile
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'role': {'required': True},
        }

    def validate(self, attrs):
        """Dynamically enforce required fields based on role"""
        role = attrs.get('role')

        if role == 'employer':
            if not attrs.get('company_name'):
                raise ValidationError({"company_name": "This field is required for employers."})
            if not attrs.get('industry'):
                raise ValidationError({"industry": "This field is required for users."})
        if role == 'user':
            if not attrs.get('first_name'):
                raise ValidationError({"first_name": "This field is required for user."})
            if not attrs.get('last_name'):
                raise ValidationError({"last_name": "This field is required for users."})
            attrs.pop('company_name', None)
            attrs.pop('industry', None)
        return attrs

    def create(self, validated_data):
        """Handle user creation"""
        password = validated_data.pop('password')
        groups = validated_data.pop('groups', [])
        user_permissions = validated_data.pop('user_permissions', [])
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        user.groups.set(groups)
        user.user_permissions.set(user_permissions)
        return user
    
class UserProfileDisplaySerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        exclude = ["company_name", "industry", "groups", "user_permissions", "password", "createdAt"]
        extra_kwargs = {
            'updatedAt': {'read_only': True},
            'is_staff': {'read_only': True},
            'is_superuser': {'read_only': True},
            'role': {'read_only': True},
            'password': {'read_only': True},
            'groups': {'read_only': True},
            'user_permissions': {'read_only': True},
        }
class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the UserProfile model"""
    user = UserProfileDisplaySerializer()
    class Meta:
        model = UserProfile
        fields = '__all__'

    def update(self, instance, validated_data):
        """Update both User and UserProfile."""
        user_data = validated_data.pop("user", None)
        user_instance = instance.user

        if user_data:
            for attr, value in user_data.items():
                setattr(user_instance, attr, value)
            user_instance.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
    
class EmployerProfileDisplaySerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        exclude = ["groups", "user_permissions", "password", "createdAt"]
        extra_kwargs = {
            'updatedAt': {'read_only': True},
            'is_staff': {'read_only': True},
            'is_superuser': {'read_only': True},
            'role': {'read_only': True},
            'password': {'read_only': True},
            'groups': {'read_only': True},
            'user_permissions': {'read_only': True},
        }

class EmployerProfileSerializer(serializers.ModelSerializer):
    """"Serializer for Employer"""
    user = EmployerProfileDisplaySerializer()
    class Meta:
        model = EmployerProfile
        fields = '__all__'

    def update(self, instance, validated_data):
        """Update both Employer and EmployerProfile."""
        user_data = validated_data.pop("user", None)
        user_instance = instance.user

        if user_data:
            for attr, value in user_data.items():
                setattr(user_instance, attr, value)
            user_instance.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

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
