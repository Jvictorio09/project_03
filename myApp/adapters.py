"""
Custom allauth adapters for multi-tenancy integration
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from .models import Company
from .signals import create_default_company_for_user
import logging

logger = logging.getLogger('myApp')


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter for handling multi-tenancy
    """
    
    def save_user(self, request, user, form, commit=True):
        """
        Save user and create default company if needed
        """
        user = super().save_user(request, user, form, commit)
        
        if commit:
            # Create default company for new user
            company = create_default_company_for_user(user)
            if company:
                # Store company in session
                request.session['company_id'] = str(company.id)
                
        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter for Google OAuth integration
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Handle pre-login logic for social accounts
        """
        try:
            user = sociallogin.user
            email = user.email
            
            if email:
                # Try to find existing user by email
                existing_user = User.objects.filter(email=email).first()
                
                if existing_user and existing_user != user:
                    # Link social account to existing user
                    sociallogin.user = existing_user
                    
                    # Ensure user has a company
                    if not hasattr(existing_user, 'company') or not existing_user.company:
                        company = create_default_company_for_user(existing_user)
                        if company:
                            request.session['company_id'] = str(company.id)
                            
        except Exception as e:
            logger.error(f"Error in pre_social_login: {str(e)}")
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user data from social account
        """
        user = super().populate_user(request, sociallogin, data)
        
        try:
            # Extract additional data from Google
            if sociallogin.account.provider == 'google':
                extra_data = sociallogin.account.extra_data
                
                # Set first and last name if available
                if 'given_name' in extra_data:
                    user.first_name = extra_data.get('given_name', '')
                if 'family_name' in extra_data:
                    user.last_name = extra_data.get('family_name', '')
                
                # Set username to email if not set
                if not user.username:
                    user.username = user.email
                    
        except Exception as e:
            logger.error(f"Error populating user data: {str(e)}")
            
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save user and handle company assignment
        """
        user = super().save_user(request, sociallogin, form)
        
        try:
            # Create default company for new user
            company = create_default_company_for_user(user)
            if company:
                # Store company in session
                request.session['company_id'] = str(company.id)
                
                logger.info(f"Created company {company.name} for Google OAuth user {user.email}")
                
        except Exception as e:
            logger.error(f"Error saving social user: {str(e)}")
            
        return user
