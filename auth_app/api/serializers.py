from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate
from rest_framework import serializers
from core.utils.validators import (
    validate_email_format,
    validate_email_unique,
    validate_password_strength,
    validate_non_empty,
)


class RegisterSerializer(serializers.Serializer):
    """Serializer that validates registration input and creates an inactive user"""
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirmed_password = serializers.CharField(write_only=True, trim_whitespace=False)
    id = serializers.IntegerField(read_only=True)
    token = serializers.CharField(read_only=True)

    def validate_email(self, value: str) -> str:
        """Validates that the email is non-empty, properly formatted, and unique"""
        email = validate_non_empty(value, 'email')
        validate_email_format(email)
        validate_email_unique(email)
        return email  

    def validate_password(self, value: str) -> str:
        """Validates that the password is non-empty and meets strength requirements"""        
        pwd = validate_non_empty(value, 'password')
        validate_password_strength(pwd)
        return pwd  

    def validate(self, attrs):
        """Validates that password and confirmed_password match"""
        if attrs.get('password') != attrs.get('confirmed_password'):
            raise serializers.ValidationError({'confirmed_password': 'Passwords do not match.'})
        return attrs  

    def create(self, validated_data):
        """Creates an inactive user and generates an activation token"""
        email = validated_data['email']
        password = validated_data['password']
        username = email
        user = User.objects.create_user(
            username=username,  
            email=email,
            password=password,
            is_active=False  
        )
        token = default_token_generator.make_token(user)  
        self._demo_token = token  
        self._created_user = user  
        return user  

    def to_representation(self, instance):
        """Custom representation to include user id, email, and activation token"""        
        return {
            'user': {
                'id': instance.id,  
                'email': instance.email,  
            },
            'token': getattr(self, '_demo_token', ''),  
        }


class LoginSerializer(serializers.Serializer):
    """Validates login payload and returns the authenticated user in .validated_data['user']"""
    email = serializers.EmailField(write_only=True)  
    password = serializers.CharField(write_only=True, trim_whitespace=False)  

    def validate(self, attrs):
        """Validates credentials and authenticates the user"""
        email = validate_non_empty(attrs.get('email', ''), 'email')  
        validate_email_format(email)  
        password = validate_non_empty(attrs.get('password', ''), 'password')  
        user = authenticate(username=email, password=password)  
        if user is None:
            raise serializers.ValidationError({'detail': 'Invalid credentials.'})
        if not user.is_active:
            raise serializers.ValidationError({'detail': 'Account is inactive. Please activate your account.'})
        attrs['user'] = user  
        return attrs  
    
    
class PasswordResetRequestSerializer(serializers.Serializer):
    """Validates the password-reset request payload"""
    email = serializers.EmailField(write_only=True)  

    def validate_email(self, value: str) -> str:
        """Validates that the email is non-empty and properly formatted"""
        email = validate_non_empty(value, 'email')  
        validate_email_format(email)  
        return email  
    
    
class PasswordResetConfirmSerializer(serializers.Serializer):
    """Validates the new password payload for password reset confirm"""
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)  
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)  

    def validate_new_password(self, value: str) -> str:
        """Validates that the new password is non-empty and meets strength requirements""" 
        pwd = validate_non_empty(value, 'new_password')  
        validate_password_strength(pwd)  
        return pwd  

    def validate(self, attrs):
        """Validates that new_password and confirm_password match"""
        if attrs.get('new_password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})  
        return attrs  