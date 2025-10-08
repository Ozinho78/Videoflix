import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from video_app.models import Video


@pytest.fixture
def active_user(db):
    """
    Fixture that creates and returns an active user
    - is_active=True is important, otherwise login would return 400
    - Username is set to the email for compatibility with authenticate()
    """
    User = get_user_model()
    return User.objects.create_user(
        username='active@example.com',
        email='active@example.com',
        password='StrongP@ssw0rd',
        is_active=True
    )


@pytest.fixture
def api_client():
    """Returns a fresh DRF APIClient for each test"""
    return APIClient()


@pytest.mark.django_db
def test_video_list_requires_authentication(api_client):
    """
    Unauthenticated requests must be rejected
    In our CookieJWTAuthentication setup:
    - No cookie -> no user -> IsAuthenticated denies access
    - DRF returns 403 Forbidden (not 401)
    """
    url = reverse('video-list')             
    response = api_client.get(url)          
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_video_list_returns_videos_when_authenticated(api_client, active_user):
    """Authenticated users (with access_token cookie) should get 200 + a list of videos"""
    login_url = reverse('login')            
    login_resp = api_client.post(
        login_url,
        {'email': active_user.email, 'password': 'StrongP@ssw0rd'},
        format='json'
    )
    assert login_resp.status_code == status.HTTP_200_OK
    assert 'access_token' in login_resp.cookies  
    api_client.cookies = login_resp.cookies
    Video.objects.create(
        title='Movie Title',
        description='Movie Description',
        category='Drama',
        file='videos/test1.mp4'
    )
    Video.objects.create(
        title='Another Movie',
        description='Another Description',
        category='Romance',
        file='videos/test2.mp4'
    )
    url = reverse('video-list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    first = data[0]
    assert 'id' in first
    assert 'created_at' in first
    assert 'title' in first
    assert 'description' in first
    assert 'thumbnail_url' in first
    assert 'category' in first


@pytest.mark.django_db
def test_video_list_empty_when_no_items(api_client, active_user):
    """Authenticated request should return an empty list (200) if no videos exist"""
    login_url = reverse('login')
    login_resp = api_client.post(
        login_url,
        {'email': active_user.email, 'password': 'StrongP@ssw0rd'},
        format='json'
    )
    assert login_resp.status_code == status.HTTP_200_OK
    api_client.cookies = login_resp.cookies    
    url = reverse('video-list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []