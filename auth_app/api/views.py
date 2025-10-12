from django.contrib.auth import login  
from django.shortcuts import render
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode  
from django.utils.encoding import force_bytes         
from django.contrib.auth.models import User  
from django.contrib.auth.tokens import default_token_generator  
from django.utils.http import urlsafe_base64_encode  
from django.utils.encoding import force_bytes  
from django.conf import settings  
from django.core.mail import send_mail  
from rest_framework.views import APIView  
from rest_framework.response import Response  
from rest_framework import status  
from auth_app.tasks import send_activation_email_async, send_password_reset_email_async
from auth_app.api.serializers import RegisterSerializer, LoginSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer  
from auth_app.emails import send_activation_email, send_password_reset_email  
import secrets  
from auth_app.jwt_utils import create_access_token, create_refresh_token  
from auth_app.jwt_utils import decode_token, create_access_token, _hash  
from auth_app.models import BlacklistedToken  


class RegisterView(APIView):
    """POST /api/register/
    Creates an inactive user, sends activation email, returns demo token
    """
    authentication_classes = []  
    permission_classes = []  

    def post(self, request, *args, **kwargs):
        """Handles user registration"""        
        serializer = RegisterSerializer(data=request.data)  
        serializer.is_valid(raise_exception=True)  
        user = serializer.save()  
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))  
        token = default_token_generator.make_token(user)  
        # send_activation_email(user, uidb64, token)          
        send_activation_email_async(user, uidb64, token)
        return Response(serializer.data, status=status.HTTP_201_CREATED)  


class ActivateView(APIView):
    """
    GET /api/activate/<uidb64>/<token>/
    Activates a user account if the token matches
    """
    authentication_classes = []  
    permission_classes = []  

    def get(self, request, uidb64: str, token: str, *args, **kwargs):
        """Handles account activation"""
        try:
            uid = int(urlsafe_base64_decode(uidb64).decode('utf-8'))  
            user = User.objects.get(pk=uid)  
        except Exception:
            return Response({'message': 'Activation failed.'}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({'message': 'Activation failed.'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            user.is_active = True  
            user.save(update_fields=['is_active'])  
        return Response({'message': 'Account successfully activated.'}, status=status.HTTP_200_OK)


import secrets  


class LoginView(APIView):
    """
    POST /api/login/
    Authenticates the user and sets HttpOnly JWT cookies (access + refresh)
    Returns a demo body per spec (frontend uses HttpOnly cookies, not the body)
    """
    authentication_classes = []  
    permission_classes = []      

    def post(self, request, *args, **kwargs):
        """Handles user login"""
        serializer = LoginSerializer(data=request.data)  
        serializer.is_valid(raise_exception=True)        
        user = serializer.validated_data['user']         
        login(request, user)                              
        access = create_access_token(user)               
        refresh = create_refresh_token(user)             
        secure = not getattr(settings, 'DEBUG', True)    
        access_max_age = int(getattr(settings, 'ACCESS_TOKEN_LIFETIME_MINUTES', 15)) * 60
        refresh_max_age = int(getattr(settings, 'REFRESH_TOKEN_LIFETIME_DAYS', 7)) * 24 * 60 * 60
        resp = Response(
            {
                'detail': 'Login successful',                 
                'user': {'id': user.id, 'username': user.username},  
            },
            status=status.HTTP_200_OK
        )
        resp.set_cookie(
            'access_token', access,
            max_age=access_max_age, httponly=True, secure=secure, samesite='Lax', path='/'
        )
        resp.set_cookie(
            'refresh_token', refresh,
            max_age=refresh_max_age, httponly=True, secure=secure, samesite='Lax', path='/'
        )
        return resp  
    
    
class RefreshTokenView(APIView):
    """
    POST /api/token/refresh/
    Reads HttpOnly refresh_token cookie, validates it, rotates the access token
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        """Handles token refresh"""
        raw = request.COOKIES.get('refresh_token')  
        if not raw:
            return Response({'detail': 'Refresh token missing.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            payload = decode_token(raw, expected_type='refresh')  
            user_id = payload.get('sub')                          
            user = User.objects.get(pk=user_id)                   
        except Exception:
            return Response({'detail': 'Invalid refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)
        access = create_access_token(user)  
        access_max_age = int(getattr(settings, 'ACCESS_TOKEN_LIFETIME_MINUTES', 15)) * 60  
        secure = not getattr(settings, 'DEBUG', True)  
        resp = Response({'detail': 'Token refreshed', 'access': access}, status=status.HTTP_200_OK)
        resp.set_cookie(
            'access_token', access,
            max_age=access_max_age, httponly=True, secure=secure, samesite='Lax', path='/'
        )
        return resp


class LogoutView(APIView):
    """
    POST /api/logout/
    Invalidates the refresh token (blacklist), deletes auth cookies, returns a spec-compliant message
    """
    authentication_classes = []  
    permission_classes = []      

    def post(self, request, *args, **kwargs):
        """Handles user logout"""
        raw = request.COOKIES.get('refresh_token')  
        if not raw:
            return Response({'detail': 'Refresh token missing.'}, status=status.HTTP_400_BAD_REQUEST)
        user = None  
        try:
            payload = decode_token(raw, expected_type='refresh')  
            user_id = payload.get('sub')
            user = User.objects.filter(pk=user_id).first()
        except Exception:
            pass
        
        BlacklistedToken.objects.get_or_create(token_hash=_hash(raw), defaults={'user': user})
        resp = Response(
            {'detail': 'Logout successful! All tokens will be deleted. Refresh token is now invalid.'},
            status=status.HTTP_200_OK
        )
        resp.delete_cookie('access_token', path='/')
        resp.delete_cookie('refresh_token', path='/')
        resp.delete_cookie('sessionid', path='/')  
        return resp
    
    
class PasswordResetRequestView(APIView):
    """
    POST /api/password_reset/
    If the email exists, send a password-reset email. Always return 200 with a generic message
    """
    authentication_classes = []  
    permission_classes = []  

    def post(self, request, *args, **kwargs):
        """Handles password reset request"""
        serializer = PasswordResetRequestSerializer(data=request.data)  
        serializer.is_valid(raise_exception=True)  
        email = serializer.validated_data['email']  
        user = User.objects.filter(email__iexact=email).first()  
        if user:
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))  
            token = default_token_generator.make_token(user)  
            # send_password_reset_email(user, uidb64, token)
            send_password_reset_email_async(user, uidb64, token)
        return Response(
            {'detail': 'An email has been sent to reset your password.'},
            status=status.HTTP_200_OK
        )
        
        
class PasswordResetConfirmView(APIView):
    """
    POST /api/password_confirm/<uidb64>/<token>/
    Validates token + uid and sets the new password on success
    """
    authentication_classes = []  
    permission_classes = []  

    def post(self, request, uidb64: str, token: str, *args, **kwargs):
        """Handles password reset confirmation"""
        try:
            uid = int(urlsafe_base64_decode(uidb64).decode('utf-8'))  
        except Exception:
            return Response({'detail': 'Invalid or expired reset link.'}, status=status.HTTP_400_BAD_REQUEST)  
        try:
            user = User.objects.get(pk=uid)  
        except User.DoesNotExist:
            return Response({'detail': 'Invalid or expired reset link.'}, status=status.HTTP_400_BAD_REQUEST)  
        if not default_token_generator.check_token(user, token):  
            return Response({'detail': 'Invalid or expired reset link.'}, status=status.HTTP_400_BAD_REQUEST)  
        serializer = PasswordResetConfirmSerializer(data=request.data)  
        serializer.is_valid(raise_exception=True)  
        new_password = serializer.validated_data['new_password']  
        user.set_password(new_password)  
        user.save(update_fields=['password'])  
        return Response({'detail': 'Your Password has been successfully reset.'}, status=status.HTTP_200_OK)
    
class PasswordResetHTMLView(APIView):
    """
    GET /api/password_reset_page/<uidb64>/<token>/
    Displays a backend-rendered HTML page where the user can set a new password.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = int(urlsafe_base64_decode(uidb64).decode('utf-8'))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({'detail': 'Invalid or expired reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        return render(request, 'auth_app/password_reset_form.html', {'uidb64': uidb64, 'token': token})

    def post(self, request, uidb64, token, *args, **kwargs):
        """Handles form submission from the rendered page"""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data['new_password']

        try:
            uid = int(urlsafe_base64_decode(uidb64).decode('utf-8'))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({'detail': 'Invalid or expired reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=['password'])
        return render(request, 'auth_app/password_reset_done.html', {'user': user})