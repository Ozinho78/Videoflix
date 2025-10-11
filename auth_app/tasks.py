"""Background tasks for sending emails asynchronously via django_rq"""
from django_rq import enqueue
from auth_app.emails import send_activation_email, send_password_reset_email


def send_activation_email_async(user, uidb64, token):
    """Enqueue activation email sending to background worker"""
    enqueue(send_activation_email, user, uidb64, token)

def send_password_reset_email_async(user, uidb64, token):
    """Enqueue password reset email sending to background worker"""
    enqueue(send_password_reset_email, user, uidb64, token)