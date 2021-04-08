from django.core.mail import EmailMessage


def send_email(subject, body, from_email, to, **kwargs):
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=to,
        **kwargs
    )
    email.send()
