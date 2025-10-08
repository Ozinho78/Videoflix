import pytest  
from django.contrib.auth.models import User  
from django.core import mail  
from django.test.utils import override_settings  
from rest_framework.test import APIClient  


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',  
    FRONTEND_BASE_URL='http://127.0.0.1:5500'  
)
def test_password_reset_sends_mail_when_user_exists_and_returns_200():
    """Happy path: known email sends reset email and returns 200"""
    u = User.objects.create_user(username='reset.me@example.com', email='reset.me@example.com',
                                 password='StrongP@ssw0rd', is_active=True)
    client = APIClient()  
    res = client.post('/api/password_reset/', {'email': 'reset.me@example.com'}, format='json')  
    assert res.status_code == 200
    assert res.json()['detail'].startswith('An email has been sent')
    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert 'Reset your Videoflix password' in msg.subject
    assert 'uid=' in msg.body and 'token=' in msg.body
    assert msg.alternatives and msg.alternatives[0][1] == 'text/html'


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
def test_password_reset_unknown_email_still_returns_200_but_sends_nothing():
    """Unknown email returns 200 but sends no email (to avoid user enumeration)"""
    client = APIClient()
    res = client.post('/api/password_reset/', {'email': 'nobody@example.com'}, format='json')
    assert res.status_code == 200
    assert len(mail.outbox) == 0  


@pytest.mark.django_db
def test_password_reset_requires_valid_email_format():
    """Badly formed email returns 400 and does not send email"""
    client = APIClient()
    res = client.post('/api/password_reset/', {'email': 'not-an-email'}, format='json')
    assert res.status_code == 400  