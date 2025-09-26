from django.contrib.auth.models import User  # User model
from django.contrib.auth.tokens import default_token_generator  # Token generator (same as in serializer)
from django.utils.http import urlsafe_base64_encode  # Safely encode the user id for URLs
from django.utils.encoding import force_bytes  # Convert integer id to bytes for encoding
from django.conf import settings  # Access project settings (e.g., EMAIL_*, FRONTEND URL)
from django.core.mail import send_mail  # Simple email sending helper
from rest_framework.views import APIView  # Base class for API views
from rest_framework.response import Response  # HTTP response wrapper
from rest_framework import status  # HTTP status codes
from .serializers import RegisterSerializer  # The serializer we just created


class RegisterView(APIView):
    """
    POST /api/register/
    Creates an inactive user, sends activation email, returns demo token.
    """

    authentication_classes = []  # Registration is public
    permission_classes = []  # No permissions required

    def post(self, request, *args, **kwargs):
        # Initialize serializer with request data
        serializer = RegisterSerializer(data=request.data)  # Bind input

        # Validate input according to serializer rules
        serializer.is_valid(raise_exception=True)  # Raises 400 with details on failure

        # Create the user and generate token (handled inside serializer.create)
        user = serializer.save()  # Persists the inactive user

        # Build activation payload parts
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))  # Encoded user id for URLs
        token = default_token_generator.make_token(user)  # Fresh activation token

        # Compose an activation link. In a real app you may point this to your frontend.
        # Fallback to localhost frontend if setting is missing.
        frontend_base = getattr(settings, 'FRONTEND_BASE_URL', 'http://127.0.0.1:5500')  # Simple default
        activation_link = f'{frontend_base}/activate.html?uid={uidb64}&token={token}'  # Query params for FE

        # Prepare the email subject and body (plain text is sufficient here)
        subject = 'Activate your Videoflix account'  # Email subject line
        message = (
            'Hi,\n\n'
            'Thanks for registering at Videoflix. Please activate your account by clicking the link below:\n\n'
            f'{activation_link}\n\n'
            'If you did not sign up, you can ignore this email.\n'
        )  # Simple text body with the activation link

        # Determine sender and recipient
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@videoflix.local')  # Sender fallback
        recipient_list = [user.email]  # Send to the registering user

        # Send the activation email (works with console backend during development)
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)  # Raise on failure

        # Return the demo response shape with 201 Created
        return Response(serializer.data, status=status.HTTP_201_CREATED)  # Matches your spec
