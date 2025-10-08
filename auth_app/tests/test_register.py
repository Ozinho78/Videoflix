import pytest  
import re  
from django.contrib.auth.models import User  
from django.core import mail  
from rest_framework.test import APIClient  
from django.test.utils import override_settings  


@pytest.mark.django_db
def test_register_success_creates_inactive_user_and_sends_email():
    """Happy path: valid data creates inactive user, sends email, returns 201 with user and token"""
    client = APIClient()  
    payload = {
        'email': 'user@example.com',
        'password': 'StrongP@ssw0rd',
        'confirmed_password': 'StrongP@ssw0rd',
    }  
    response = client.post('/api/register/', payload, format='json')  
    assert response.status_code == 201  
    data = response.json()  
    assert 'user' in data and 'token' in data  
    assert data['user']['email'] == 'user@example.com'  
    u = User.objects.get(email='user@example.com')  
    assert u.is_active is False  
    assert len(mail.outbox) == 1  
    assert 'Confirm your email' in mail.outbox[0].subject  
    assert 'activate.html' in mail.outbox[0].body  
    assert 'token=' in mail.outbox[0].body and 'uid=' in mail.outbox[0].body  


@pytest.mark.django_db
def test_register_passwords_must_match():
    """Mismatched passwords return 400 and do not create user"""
    client = APIClient()  
    payload = {
        'email': 'x@example.com',
        'password': 'StrongP@ssw0rd',
        'confirmed_password': 'Mismatch123!',
    }  
    response = client.post('/api/register/', payload, format='json')  
    assert response.status_code == 400  
    assert 'confirmed_password' in response.json()  


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',  
    FRONTEND_BASE_URL='http://127.0.0.1:5500'                       
)
def test_register_sends_html_activation_email():
    """Registration sends HTML email with activation link containing uid and token"""
    client = APIClient()
    payload = {
        'email': 'user@example.com',
        'password': 'StrongP@ssw0rd',
        'confirmed_password': 'StrongP@ssw0rd',
    }
    res = client.post('/api/register/', payload, format='json')
    assert res.status_code == 201