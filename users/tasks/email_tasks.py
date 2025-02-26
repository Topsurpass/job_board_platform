import logging
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from django.template.loader import render_to_string
import datetime

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def send_welcome_email(self, recipient_email: str, first_name: str) -> None:
    """Asynchronously sends a styled welcome email to new users with retry capabilities."""
    try:
        # Email configuration
        subject = "🎉 Welcome to EaseWork - Find your desired jobs with ease!"
        from_email = f"EaseWork Team <{settings.DEFAULT_FROM_EMAIL}>"
        
        # Context for template rendering
        context = {
            'first_name': first_name,
            'support_email': settings.SUPPORT_EMAIL,
            'company_name': "EaseWork",
            'current_year': datetime.datetime.now().year
        }

        html_content = render_to_string('emails/welcome.html', context)
        
        # Create plain text version by stripping HTML tags
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[recipient_email],
            reply_to=[settings.EMAIL_HOST_USER]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Add email headers for analytics
        email.extra_headers = {
            'X-Email-Category': 'Welcome',
            'X-Email-Type': 'Transactional'
        }

        email.send(fail_silently=False)
        
        logger.info(f"Successfully sent welcome email to {recipient_email}")
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {recipient_email}: {str(e)}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
    

@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
def send_employer_welcome_email(self, recipient_email: str, company_name: str) -> None:
    """Asynchronously sends a styled welcome email to new employers with retry capabilities."""
    try:
        subject = "🚀 Welcome to EaseWork - Start Hiring the Best Talent!"
        from_email = f"EaseWork Team <{settings.DEFAULT_FROM_EMAIL}>"
        
        # Context for template rendering
        context = {
            'company_name': company_name,
            'support_email': settings.SUPPORT_EMAIL,
            'platform_name': "EaseWork",
            'current_year': datetime.datetime.now().year
        }

        html_content = render_to_string('emails/employer_welcome.html', context)
        
        # Create plain text version by stripping HTML tags
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[recipient_email],
            reply_to=[settings.EMAIL_HOST_USER]
        )
        email.attach_alternative(html_content, "text/html")
        
        email.extra_headers = {
            'X-Email-Category': 'Employer Welcome',
            'X-Email-Type': 'Transactional'
        }

        email.send(fail_silently=False)
        
        logger.info(f"Successfully sent employer welcome email to {recipient_email}")
        
    except Exception as e:
        logger.error(f"Failed to send employer welcome email to {recipient_email}: {str(e)}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
