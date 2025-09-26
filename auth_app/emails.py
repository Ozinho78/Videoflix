from django.conf import settings  # Zugriff auf DEFAULT_FROM_EMAIL und FRONTEND_BASE_URL
from django.core.mail import EmailMultiAlternatives  # Ermöglicht Text + HTML in einer Mail
from django.template.loader import render_to_string  # Rendert unsere Templates zu HTML/Text


def send_activation_email(user, uidb64: str, token: str) -> None:
    """
    Compose and send the activation email with both plain text and HTML parts.
    """
    # 1) Subject line for the email
    subject = 'Confirm your email for Videoflix'  # Klarer Betreff

    # 2) From and to
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@videoflix.local')  # Fallback Sender
    to = [user.email]  # Empfänger ist der registrierte User

    # 3) Build activation link that points to the FRONTEND page
    frontend_base = getattr(settings, 'FRONTEND_BASE_URL', 'http://127.0.0.1:5500')  # Fallback für Dev
    activation_link = f'{frontend_base}/activate.html?uid={uidb64}&token={token}'  # FE verarbeitet & leitet weiter

    # 4) Context for the templates
    context = {
        'user_email': user.email,           # Für die Anrede / Anzeige
        'activation_link': activation_link, # Für Button/URL
        'frontend_base': frontend_base,     # Für Logo/Assets, wenn gewünscht
    }

    # 5) Render plain text and HTML bodies from templates
    text_body = render_to_string('emails/activation_email.txt', context)  # Text-Fallback für Clients ohne HTML
    html_body = render_to_string('emails/activation_email.html', context)  # Schicke HTML-Version

    # 6) Build a multi-part email (text + html alternative)
    message = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=to)  # Grundmail
    message.attach_alternative(html_body, 'text/html')  # HTML als Alternative anhängen

    # 7) Send it (synchron; später ggf. per RQ/Celery asynchron versenden)
    message.send(fail_silently=False)  # In Dev/Tests wirft Fehler -> einfacher zu debuggen
