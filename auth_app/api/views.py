from django.contrib.auth import login  # To create session on successful login
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode  # UID kodieren
from django.utils.encoding import force_bytes         # ID -> bytes
from django.contrib.auth.models import User  # User model
from django.contrib.auth.tokens import default_token_generator  # Token generator (same as in serializer)
from django.utils.http import urlsafe_base64_encode  # Safely encode the user id for URLs
from django.utils.encoding import force_bytes  # Convert integer id to bytes for encoding
from django.conf import settings  # Access project settings (e.g., EMAIL_*, FRONTEND URL)
from django.core.mail import send_mail  # Simple email sending helper
from rest_framework.views import APIView  # Base class for API views
from rest_framework.response import Response  # HTTP response wrapper
from rest_framework import status  # HTTP status codes
from auth_app.api.serializers import RegisterSerializer, LoginSerializer    # The serializer we just created
from auth_app.emails import send_activation_email
import secrets  # For a simple demo token string
from auth_app.jwt_utils import create_access_token, create_refresh_token  # Our JWT helpers
from auth_app.jwt_utils import decode_token, create_access_token, _hash  # JWT helpers and token hashing
from auth_app.models import BlacklistedToken  # Persist blacklisted refresh tokens


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

        # # Compose an activation link. In a real app you may point this to your frontend.
        # # Fallback to localhost frontend if setting is missing.
        # frontend_base = getattr(settings, 'FRONTEND_BASE_URL', 'http://127.0.0.1:5500')  # Simple default
        # activation_link = f'{frontend_base}/activate.html?uid={uidb64}&token={token}'  # Query params for FE

        # # Prepare the email subject and body (plain text is sufficient here)
        # subject = 'Activate your Videoflix account'  # Email subject line
        # message = (
        #     'Hi,\n\n'
        #     'Thanks for registering at Videoflix. Please activate your account by clicking the link below:\n\n'
        #     f'{activation_link}\n\n'
        #     'If you did not sign up, you can ignore this email.\n'
        # )  # Simple text body with the activation link

        # # Determine sender and recipient
        # from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@videoflix.local')  # Sender fallback
        # recipient_list = [user.email]  # Send to the registering user

        # # Send the activation email (works with console backend during development)
        # send_mail(subject, message, from_email, recipient_list, fail_silently=False)  # Raise on failure
        
        send_activation_email(user, uidb64, token)          # HTML-Mail versenden

        # Return the demo response shape with 201 Created
        return Response(serializer.data, status=status.HTTP_201_CREATED)  # Matches your spec


class ActivateView(APIView):
    """
    GET /api/activate/<uidb64>/<token>/
    Activates a user account if the token matches.
    """
    authentication_classes = []  # Public endpoint
    permission_classes = []  # No permissions

    def get(self, request, uidb64: str, token: str, *args, **kwargs):
        try:
            # 1) Decode the uid from base64 to integer
            uid = int(urlsafe_base64_decode(uidb64).decode('utf-8'))  # May raise ValueError/UnicodeError
            # 2) Look up the user by primary key
            user = User.objects.get(pk=uid)  # May raise DoesNotExist
        except Exception:
            # Return generic 400 to avoid leaking user enumeration details
            return Response({'message': 'Activation failed.'}, status=status.HTTP_400_BAD_REQUEST)

        # 3) Validate the token for this user
        if not default_token_generator.check_token(user, token):
            return Response({'message': 'Activation failed.'}, status=status.HTTP_400_BAD_REQUEST)

        # 4) Activate the user if not already active
        if not user.is_active:
            user.is_active = True  # Flip active flag
            user.save(update_fields=['is_active'])  # Persist

        # 5) Return success message per spec
        return Response({'message': 'Account successfully activated.'}, status=status.HTTP_200_OK)


import secrets  # For a simple demo token string


class LoginView(APIView):
    """
    POST /api/login/
    Authenticates the user and sets HttpOnly JWT cookies (access + refresh).
    Returns a demo body per spec (frontend uses HttpOnly cookies, not the body).
    """
    authentication_classes = []  # Public endpoint
    permission_classes = []      # No permissions required

    def post(self, request, *args, **kwargs):
        # 1) Validate payload and authenticate
        serializer = LoginSerializer(data=request.data)  # Bind JSON body
        serializer.is_valid(raise_exception=True)        # 400 on invalid

        # 2) Get the authenticated user (serializer.authenticate did the work)
        user = serializer.validated_data['user']         # Authenticated user

        # 3) Optionally create a Django session (not required for JWT cookies)
        #    If you don't want a session, comment the next line.
        login(request, user)                              # Creates a sessionid cookie (HttpOnly)

        # 4) Create JWTs
        access = create_access_token(user)               # Short-lived token
        refresh = create_refresh_token(user)             # Longer-lived token

        # 5) Set HttpOnly cookies; secure flags depend on DEBUG for local dev
        secure = not getattr(settings, 'DEBUG', True)    # True in production
        # Max-Age values should match your lifetimes (defaults: 15 min / 7 days)
        access_max_age = int(getattr(settings, 'ACCESS_TOKEN_LIFETIME_MINUTES', 15)) * 60
        refresh_max_age = int(getattr(settings, 'REFRESH_TOKEN_LIFETIME_DAYS', 7)) * 24 * 60 * 60

        # 6) Shape the response per your spec
        resp = Response(
            {
                'detail': 'Login successful',                 # Spec text
                'user': {'id': user.id, 'username': user.username},  # Spec wants "username"
            },
            status=status.HTTP_200_OK
        )

        # 7) Attach cookies (HttpOnly, SameSite=Lax is FE-friendly; tweak as needed)
        resp.set_cookie(
            'access_token', access,
            max_age=access_max_age, httponly=True, secure=secure, samesite='Lax', path='/'
        )
        resp.set_cookie(
            'refresh_token', refresh,
            max_age=refresh_max_age, httponly=True, secure=secure, samesite='Lax', path='/'
        )

        return resp  # Done
    
    
class RefreshTokenView(APIView):
    """
    POST /api/token/refresh/
    Reads HttpOnly refresh_token cookie, validates it, rotates the access token.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        # 1) Get refresh cookie (required by spec)
        raw = request.COOKIES.get('refresh_token')  # HttpOnly cookie with refresh token
        if not raw:
            # Spec: 400 when refresh token is missing
            return Response({'detail': 'Refresh token missing.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 2) Decode and require type 'refresh' (raises if invalid/expired/wrong type)
            payload = decode_token(raw, expected_type='refresh')  # Validates signature and exp
            user_id = payload.get('sub')                          # User id from token
            user = User.objects.get(pk=user_id)                   # Ensure user exists
        except Exception:
            # Spec: 401 when refresh token is invalid
            return Response({'detail': 'Invalid refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)

        # 3) Issue a new short-lived access token
        access = create_access_token(user)  # Fresh access JWT

        # 4) Set cookie attributes (keep consistent with your login view)
        access_max_age = int(getattr(settings, 'ACCESS_TOKEN_LIFETIME_MINUTES', 15)) * 60  # seconds
        secure = not getattr(settings, 'DEBUG', True)  # Secure only in production

        # 5) Build response per spec: include 'access' in body for demo
        resp = Response({'detail': 'Token refreshed', 'access': access}, status=status.HTTP_200_OK)

        # 6) Also set the new access token as HttpOnly cookie
        resp.set_cookie(
            'access_token', access,
            max_age=access_max_age, httponly=True, secure=secure, samesite='Lax', path='/'
        )
        return resp


class LogoutView(APIView):
    """
    POST /api/logout/
    Invalidates the refresh token (blacklist), deletes auth cookies, returns a spec-compliant message.
    """
    authentication_classes = []  # Public endpoint; relies on refresh cookie presence
    permission_classes = []      # No permissions required

    def post(self, request, *args, **kwargs):
        # 1) Require the refresh cookie as per spec
        raw = request.COOKIES.get('refresh_token')  # Read the HttpOnly refresh token
        if not raw:
            return Response({'detail': 'Refresh token missing.'}, status=status.HTTP_400_BAD_REQUEST)

        # 2) Try to link the blacklist entry to a user (best-effort)
        user = None  # Default if we cannot decode
        try:
            payload = decode_token(raw, expected_type='refresh')  # May raise on invalid/expired/blacklisted
            user_id = payload.get('sub')
            user = User.objects.filter(pk=user_id).first()
        except Exception:
            # Even if decoding fails, we still blacklist by raw token hash to be safe
            pass

        # 3) Blacklist the (hashed) refresh token; idempotent via get_or_create
        BlacklistedToken.objects.get_or_create(token_hash=_hash(raw), defaults={'user': user})

        # 4) Build the response and delete cookies (access, refresh, session)
        resp = Response(
            {'detail': 'Logout successful! All tokens will be deleted. Refresh token is now invalid.'},
            status=status.HTTP_200_OK
        )
        # Delete cookies by setting them to empty with Max-Age=0 (browser removes them)
        resp.delete_cookie('access_token', path='/')
        resp.delete_cookie('refresh_token', path='/')
        resp.delete_cookie('sessionid', path='/')  # Optional: if you created a Django session on login

        return resp