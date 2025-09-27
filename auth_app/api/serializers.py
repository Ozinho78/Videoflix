from django.contrib.auth.models import User  # Use Django's built-in User model
from django.contrib.auth.tokens import default_token_generator  # Token generator for activation links
from django.contrib.auth import authenticate  # To validate credentials in LoginSerializer
from rest_framework import serializers  # DRF serializer base classes
from core.utils.validators import (  # Import your shared validators module
    validate_email_format,
    validate_email_unique,
    validate_password_strength,
    validate_non_empty,
)


class RegisterSerializer(serializers.Serializer):
    """
    Serializer that validates registration input and creates an inactive user.
    """
    # Public input fields
    email = serializers.EmailField(write_only=True)  # E-Mail provided by the user
    password = serializers.CharField(write_only=True, trim_whitespace=False)  # Raw password
    confirmed_password = serializers.CharField(write_only=True, trim_whitespace=False)  # Confirmation

    # Output-only fields for the demo response
    id = serializers.IntegerField(read_only=True)  # ID of the created user
    token = serializers.CharField(read_only=True)  # Activation token for demonstration

    def validate_email(self, value: str) -> str:
        # Ensure email is non-empty and trimmed
        email = validate_non_empty(value, 'email')  # Raises ValidationError if blank
        # Check email format
        validate_email_format(email)  # Raises ValidationError if invalid
        # Ensure uniqueness (case-insensitive)
        validate_email_unique(email)  # Raises ValidationError if taken
        return email  # Return normalized/trimmed email

    def validate_password(self, value: str) -> str:
        # Basic non-empty check (and strip) to be safe
        pwd = validate_non_empty(value, 'password')  # Raises if blank
        # Validate strength according to your rules
        validate_password_strength(pwd)  # Raises if weak
        return pwd  # Return the validated password

    def validate(self, attrs):
        # Ensure password and confirmed_password match
        if attrs.get('password') != attrs.get('confirmed_password'):
            raise serializers.ValidationError({'confirmed_password': 'Passwords do not match.'})  # Field-level error
        return attrs  # Return the full, validated attribute dict

    def create(self, validated_data):
        # Pull out validated fields
        email = validated_data['email']  # Already validated
        password = validated_data['password']  # Already validated

        # Use email as username to satisfy Django's default User model (username is required)
        username = email  # Simple strategy: mirror email into username

        # Create the inactive user
        user = User.objects.create_user(  # create_user handles password hashing
            username=username,  # Username (using email)
            email=email,  # Store email
            password=password,  # Raw password is hashed internally
            is_active=False  # Keep the account inactive until email activation
        )

        # Generate a one-time activation token using Django's default token generator
        token = default_token_generator.make_token(user)  # Token tied to user state

        # Attach output-only fields into serializer instance data for response
        self._demo_token = token  # Store token for use in to_representation
        self._created_user = user  # Keep reference for output fields

        return user  # DRF expects the created instance

    def to_representation(self, instance):
        # Build the demo response payload exactly as specified
        return {
            'user': {
                'id': instance.id,  # Database ID of the new user
                'email': instance.email,  # Echo the email
            },
            'token': getattr(self, '_demo_token', ''),  # Include activation token for demonstration
        }


class LoginSerializer(serializers.Serializer):
    """
    Validates login payload and returns the authenticated user in .validated_data['user'].
    """
    email = serializers.EmailField(write_only=True)  # Email input
    password = serializers.CharField(write_only=True, trim_whitespace=False)  # Raw password

    def validate(self, attrs):
        # 1) Normalize + basic checks
        email = validate_non_empty(attrs.get('email', ''), 'email')  # Non-empty email
        validate_email_format(email)  # Basic format check
        password = validate_non_empty(attrs.get('password', ''), 'password')  # Non-empty password

        # 2) Authenticate using email as username (your users are created with username=email)
        user = authenticate(username=email, password=password)  # None if invalid

        # 3) Generic error to avoid leaking which field is wrong
        if user is None:
            raise serializers.ValidationError({'detail': 'Invalid credentials.'})

        # 4) Block inactive accounts (must confirm email first)
        if not user.is_active:
            raise serializers.ValidationError({'detail': 'Account is inactive. Please activate your account.'})

        # 5) Stash user for the view
        attrs['user'] = user  # Store the user for the view
        return attrs  # Return validated attrs