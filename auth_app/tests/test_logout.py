import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from auth_app.jwt_utils import create_access_token, create_refresh_token, _hash
from auth_app.models import BlacklistedToken


@pytest.mark.django_db
def test_logout_blacklists_refresh_and_deletes_cookies():
    """Happy path: valid access and refresh tokens in cookies log out user, blacklist refresh, and delete cookies"""
    u = User.objects.create_user(username='bye@example.com', email='bye@example.com',
                                 password='StrongP@ssw0rd', is_active=True)
    access = create_access_token(u)
    refresh = create_refresh_token(u)
    client = APIClient()
    client.cookies['access_token'] = access
    client.cookies['refresh_token'] = refresh
    res = client.post('/api/logout/', {}, format='json')
    assert res.status_code == 200
    assert res.json()['detail'].startswith('Logout successful!')
    cookie_str = res.cookies.output(header='').lower()
    assert 'access_token=' in cookie_str and ('max-age=0' in cookie_str or 'expires=' in cookie_str)
    assert 'refresh_token=' in cookie_str and ('max-age=0' in cookie_str or 'expires=' in cookie_str)
    assert BlacklistedToken.objects.filter(token_hash=_hash(refresh)).exists()


@pytest.mark.django_db
def test_logout_missing_cookie_returns_400():
    """Missing access or refresh token cookie returns 400"""
    client = APIClient()  
    res = client.post('/api/logout/', {}, format='json')
    assert res.status_code == 400


@pytest.mark.django_db
def test_refresh_after_logout_fails_due_to_blacklist():
    """After logout, using the same refresh token to get a new access token fails with 401 due to blacklist"""
    u = User.objects.create_user(username='x@example.com', email='x@example.com',
                                 password='StrongP@ssw0rd', is_active=True)
    refresh = create_refresh_token(u)
    client = APIClient()
    client.cookies['refresh_token'] = refresh
    _ = client.post('/api/logout/', {}, format='json')  
    client.cookies['refresh_token'] = refresh  
    res = client.post('/api/token/refresh/', {}, format='json')
    assert res.status_code == 401