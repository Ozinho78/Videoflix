import pytest
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_activate_success_marks_user_active_and_returns_message():
    """Happy path: valid uidb64 + token activates the user"""
    u = User.objects.create_user(username='activate.me@example.com',
                                 email='activate.me@example.com',
                                 password='StrongP@ssw0rd',
                                 is_active=False)
    uidb64 = urlsafe_base64_encode(force_bytes(u.pk))
    token = default_token_generator.make_token(u)
    client = APIClient()
    res = client.get(f'/api/activate/{uidb64}/{token}/')
    assert res.status_code == 200
    assert res.json().get('message') == 'Account successfully activated.'
    u.refresh_from_db()
    assert u.is_active is True


@pytest.mark.django_db
def test_activate_invalid_token_returns_400():
    """Invalid token (even with valid uidb64) returns 400"""
    u = User.objects.create_user(username='bad.token@example.com',
                                 email='bad.token@example.com',
                                 password='StrongP@ssw0rd',
                                 is_active=False)
    uidb64 = urlsafe_base64_encode(force_bytes(u.pk))
    bad_token = 'totally-wrong-token'
    client = APIClient()
    res = client.get(f'/api/activate/{uidb64}/{bad_token}/')
    assert res.status_code == 400
    assert 'message' in res.json()