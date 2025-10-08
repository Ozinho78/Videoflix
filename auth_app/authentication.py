from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.contrib.auth.models import User
from auth_app.jwt_utils import decode_token


class CookieJWTAuthentication(BaseAuthentication):
    """Authenticate user based on JWT stored in HttpOnly access_token cookie"""
    def authenticate(self, request):
        token = request.COOKIES.get('access_token')
        if not token:
            return None
        try:
            payload = decode_token(token, expected_type='access')
            user_id = payload.get('sub')
            user = User.objects.get(pk=user_id)
        except Exception:
            raise exceptions.AuthenticationFailed('Invalid or expired token.')
        return (user, token)