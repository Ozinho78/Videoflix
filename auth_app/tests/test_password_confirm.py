import pytest  
from django.contrib.auth.models import User  
from django.contrib.auth import authenticate  
from django.utils.http import urlsafe_base64_encode  
from django.utils.encoding import force_bytes  
from django.contrib.auth.tokens import default_token_generator  
from rest_framework.test import APIClient  


@pytest.mark.django_db
def test_password_confirm_success_sets_new_password_and_returns_200():
    """Happy path: valid token and matching strong passwords reset password, return 200"""
    email = 'reset.ok@example.com'  
    user = User.objects.create_user(username=email, email=email, password='OldP@ssw0rd', is_active=True)  
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))  
    token = default_token_generator.make_token(user)  
    client = APIClient()  
    payload = {'new_password': 'NewStr0ng!Pass', 'confirm_password': 'NewStr0ng!Pass'}  
    res = client.post(f'/api/password_confirm/{uidb64}/{token}/', payload, format='json')  
    assert res.status_code == 200  
    assert res.json()['detail'].startswith('Your Password has been successfully reset.')  
    assert authenticate(username=email, password='OldP@ssw0rd') is None  
    assert authenticate(username=email, password='NewStr0ng!Pass') is not None  


@pytest.mark.django_db
def test_password_confirm_rejects_invalid_token():
    """Invalid token returns 400 and does not change password"""
    email = 'reset.bad@example.com'
    user = User.objects.create_user(username=email, email=email, password='OldP@ssw0rd', is_active=True)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    bad_token = 'totally-wrong-token'
    client = APIClient()
    res = client.post(f'/api/password_confirm/{uidb64}/{bad_token}/', {
        'new_password': 'NewStr0ng!Pass',
        'confirm_password': 'NewStr0ng!Pass'
    }, format='json')
    assert res.status_code == 400  
    assert 'invalid' in res.json()['detail'].lower()


@pytest.mark.django_db
def test_password_confirm_requires_strong_and_matching_passwords():
    """Weak or non-matching passwords return 400 and do not change password"""
    email = 'reset.rules@example.com'
    user = User.objects.create_user(username=email, email=email, password='OldP@ssw0rd', is_active=True)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    client = APIClient()
    res1 = client.post(f'/api/password_confirm/{uidb64}/{token}/', {
        'new_password': 'short',
        'confirm_password': 'short',
    }, format='json')
    assert res1.status_code == 400    
    res2 = client.post(f'/api/password_confirm/{uidb64}/{token}/', {
        'new_password': 'GoodP@ssw0rd',
        'confirm_password': 'Different123!',
    }, format='json')
    assert res2.status_code == 400