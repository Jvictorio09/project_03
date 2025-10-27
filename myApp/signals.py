"""
Custom signals for handling Google OAuth integration with multi-tenancy
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_added
from .models import Company
from .services import EventLogger
import logging

logger = logging.getLogger('myApp')


@receiver(user_signed_up)
def handle_user_signed_up(sender, request, user, **kwargs):
    """
    Handle new user signup via Google OAuth
    """
    try:
        # Get the social account (Google)
        social_account = user.socialaccount_set.filter(provider='google').first()
        
        if social_account:
            # Extract email domain for company binding
            email_domain = user.email.split('@')[1].lower()
            
            # Try to find existing company by domain
            company = Company.objects.filter(domain=email_domain).first()
            
            if not company:
                # Create new company for this domain
                company = Company.objects.create(
                    name=f"{email_domain.title()} Real Estate",
                    domain=email_domain,
                    created_by=user
                )
                
                logger.info(f"Created new company {company.name} for domain {email_domain}")
            
            # Store company in session for middleware
            request.session['company_id'] = str(company.id)
            
            # Log the event
            EventLogger.log_event(
                company=company,
                user=user,
                event_type='user.google_signup',
                description=f'User signed up via Google OAuth',
                metadata={
                    'email_domain': email_domain,
                    'provider': 'google',
                    'social_account_id': social_account.id
                }
            )
            
            logger.info(f"User {user.email} signed up via Google OAuth, assigned to company {company.name}")
            
    except Exception as e:
        logger.error(f"Error handling Google OAuth signup: {str(e)}")


@receiver(social_account_added)
def handle_social_account_added(sender, request, sociallogin, **kwargs):
    """
    Handle when a social account is added to an existing user
    """
    try:
        user = sociallogin.user
        social_account = sociallogin.account
        
        if social_account.provider == 'google':
            # Check if user already has a company
            if hasattr(user, 'company') and user.company:
                # User already has a company, just log the event
                EventLogger.log_event(
                    company=user.company,
                    user=user,
                    event_type='user.google_linked',
                    description=f'Google account linked to existing user',
                    metadata={
                        'provider': 'google',
                        'social_account_id': social_account.id
                    }
                )
            else:
                # User doesn't have a company, try domain matching
                email_domain = user.email.split('@')[1].lower()
                company = Company.objects.filter(domain=email_domain).first()
                
                if company:
                    # Link user to existing company
                    user.company = company
                    user.save()
                    
                    request.session['company_id'] = str(company.id)
                    
                    EventLogger.log_event(
                        company=company,
                        user=user,
                        event_type='user.google_linked',
                        description=f'Google account linked, assigned to company {company.name}',
                        metadata={
                            'email_domain': email_domain,
                            'provider': 'google',
                            'social_account_id': social_account.id
                        }
                    )
                    
                    logger.info(f"Linked Google account for {user.email} to company {company.name}")
        
    except Exception as e:
        logger.error(f"Error handling social account addition: {str(e)}")


def create_default_company_for_user(user):
    """
    Create a default company for a user if they don't have one
    """
    try:
        if not hasattr(user, 'company') or not user.company:
            # Create a default company
            company = Company.objects.create(
                name=f"{user.first_name or user.username}'s Company",
                domain=user.email.split('@')[1].lower(),
                created_by=user
            )
            
            # Link user to company
            user.company = company
            user.save()
            
            logger.info(f"Created default company {company.name} for user {user.email}")
            return company
            
    except Exception as e:
        logger.error(f"Error creating default company: {str(e)}")
        return None
