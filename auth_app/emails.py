from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


def send_activation_email(user, uidb64: str, token: str) -> None:
    """Compose and send the activation email with both plain text and HTML parts"""
    subject = 'Confirm your email for Videoflix'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@videoflix.local')
    to = [user.email]
    frontend_base = getattr(settings, 'FRONTEND_BASE_URL', 'http://127.0.0.1:5500')
    activation_link = f'{frontend_base}/pages/auth/activate.html?uid={uidb64}&token={token}'
    context = {
        'user_email': user.email,
        'activation_link': activation_link,
        'frontend_base': frontend_base,
    }
    text_body = render_to_string('emails/activation_email.txt', context)
    html_body = render_to_string('emails/activation_email.html', context)
    message = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=to)
    message.attach_alternative(html_body, 'text/html')
    message.send(fail_silently=False)


def send_password_reset_email(user, uidb64: str, token: str) -> None:
    """Compose and send the password-reset email (text + HTML)"""
    subject = 'Reset your Videoflix password'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@videoflix.local')
    to = [user.email]
    frontend_base = getattr(settings, 'FRONTEND_BASE_URL', 'http://127.0.0.1:5500')
    reset_link = f'{frontend_base}/pages/auth/forgot_password.html?uid={uidb64}&token={token}'
    context = {
        'user_email': user.email,
        'reset_link': reset_link,
        'frontend_base': frontend_base,
    }
    text_body = render_to_string('emails/password_reset_email.txt', context)
    html_body = render_to_string('emails/password_reset_email.html', context)
    msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=to)
    msg.attach_alternative(html_body, 'text/html')
    msg.send(fail_silently=False)