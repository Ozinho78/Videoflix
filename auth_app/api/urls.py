from django.urls import path  # URL pattern helper
from .views import RegisterView  # Import the view

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),  # POST /api/register/
]
