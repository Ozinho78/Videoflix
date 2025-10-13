"""Endpoint URL mappings for the auth_app API"""
from django.urls import path
from auth_app.api.views import RegisterView, LoginView, ActivateView, RefreshTokenView, LogoutView, PasswordResetRequestView, PasswordResetHTMLView, PasswordResetConfirmView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('activate/<uidb64>/<token>/', ActivateView.as_view(), name='activate'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password_reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password_confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    # path('password_reset_page/<uidb64>/<token>/', PasswordResetHTMLView.as_view(), name='password-reset-page'),

]
