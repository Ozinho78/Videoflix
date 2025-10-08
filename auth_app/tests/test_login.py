import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_login_sets_jwt_cookies_and_returns_spec_body():
    """Happy path: valid credentials return 200, expected body, and set JWT cookies"""
    email = 'login.tester@example.com'
    password = 'StrongP@ssw0rd'
    u = User.objects.create_user(username=email, email=email, password=password, is_active=True)
    client = APIClient()
    res = client.post('/api/login/', {'email': email, 'password': password}, format='json')
    assert res.status_code == 200
    body = res.json()
    assert body['detail'] == 'Login successful'
    assert body['user'] == {'id': u.id, 'username': email}
    cookie_str = res.cookies.output(header='').lower()  
    assert 'access_token=' in cookie_str and 'httponly' in cookie_str
    assert 'refresh_token=' in cookie_str and 'httponly' in cookie_str


@pytest.mark.django_db
def test_login_wrong_password_yields_401_and_no_jwt_cookies():
    """Wrong password returns 401 and does not set JWT cookies"""
    email = 'wrong.pass@example.com'
    User.objects.create_user(username=email, email=email, password='CorrectP@ss1', is_active=True)
    client = APIClient()
    res = client.post('/api/login/', {'email': email, 'password': 'totallyWrong!'}, format='json')
    assert res.status_code in (400, 401)  
    cookie_str = res.cookies.output(header='').lower()
    assert 'access_token=' not in cookie_str and 'refresh_token=' not in cookie_str
