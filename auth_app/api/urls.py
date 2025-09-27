from django.urls import path  # URL pattern helper
from .views import RegisterView, LoginView, ActivateView, RefreshTokenView  # Import the view

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),  # POST /api/register/
    path('login/', LoginView.as_view(), name='login'),  # POST /api/login/
    path('activate/<uidb64>/<token>/', ActivateView.as_view(), name='activate'),  # GET /api/activate/...
    path('token/refresh/', RefreshTokenView.as_view(), name='token-refresh'),
]
