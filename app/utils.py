from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader


def make_naive(dt: datetime):
    """
    Convert a datetime object to naive (timezone-unaware) UTC datetime.
    If the datetime is already naive, it will be returned as is.
    If it has timezone info, it will be converted to UTC and then made naive.
    """
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def render_appointment_email(name, date, services, link):
    env = Environment(loader=FileSystemLoader("assets/email_templates"))
    template = env.get_template("appointment_confirmation.html")
    return template.render(name=name, date=date, services=services, link=link)
