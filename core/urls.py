"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin                 # Admin routes
from django.urls import path, include            # URL helpers
from django.conf import settings                 # Access DEBUG, MEDIA_URL/ROOT
from django.conf.urls.static import static       # Helper to serve media in dev

urlpatterns = [
    path('admin/', admin.site.urls),             # /admin/
    path('api/', include('auth_app.api.urls')),  # /api/... auth endpoints
    path('api/', include('video_app.api.urls')), # /api/... video endpoints
    path('api-auth/', include('rest_framework.urls')),  # DRF browser login
]

# Important: static() only returns patterns if settings.DEBUG is True.
# Ensure DEBUG=True in your local environment (e.g., .env) for development.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
