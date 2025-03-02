import logging
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from django.template.loader import render_to_string
import datetime

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def send_job_application_email(self, recipient_email: str, first_name: str, job_title: str, company_name: str) -> None:
    """Asynchronously sends a job application confirmation email to the user."""
    try:
        subject = f"✅ Your application for {job_title} has been submitted!"
        from_email = f"JobNest Team <{settings.DEFAULT_FROM_EMAIL}>"
        
        # Context for the email template
        context = {
            'first_name': first_name,
            'job_title': job_title,
            'company_name': company_name,
            'support_email': settings.SUPPORT_EMAIL,
            'current_year': datetime.datetime.now().year
        }

        html_content = render_to_string('emails/job_application_submitted.html', context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[recipient_email],
            reply_to=[settings.EMAIL_HOST_USER]
        )
        email.attach_alternative(html_content, "text/html")

        # Email headers for tracking
        email.extra_headers = {
            'X-Email-Category': 'Job Application',
            'X-Email-Type': 'Transactional'
        }

        email.send(fail_silently=False)
        logger.info(f"Successfully sent job application email to {recipient_email}")

    except Exception as e:
        logger.error(f"Failed to send job application email to {recipient_email}: {str(e)}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
