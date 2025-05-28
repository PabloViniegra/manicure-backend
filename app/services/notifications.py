import resend
import os


def send_notification_email(
    email: str,
    subject: str,
    html: str
):
    """
    Send an email notification using Resend API.
    Args:
        email (str): Recipient's email address.
        subject (str): Subject of the email.
        html (str): HTML body of the email.
    Returns:
        dict: Response from the Resend API containing email details.
    Raises:
        RuntimeError: If the Resend API key is not configured.
    """
    params: resend.Emails.SendParams = {
        'from': os.getenv("RESEND_FROM_EMAIL"),
        'to': [email],
        'subject': subject,
        'html': html,
    }
    email = resend.Emails.send(params)

    return email
