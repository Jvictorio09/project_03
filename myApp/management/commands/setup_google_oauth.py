"""
Management command to set up Google OAuth application
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Set up Google OAuth application for allauth'

    def handle(self, *args, **options):
        try:
            # Get or create the site
            site, created = Site.objects.get_or_create(
                id=settings.SITE_ID,
                defaults={
                    'domain': 'localhost:8000',
                    'name': 'KaTek AI'
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created site: {site.name}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Using existing site: {site.name}')
                )

            # Get Google OAuth credentials from environment
            client_id = os.getenv('GOOGLE_CLIENT_ID')
            client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                self.stdout.write(
                    self.style.ERROR(
                        'Google OAuth credentials not found in environment variables.\n'
                        'Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file.'
                    )
                )
                return

            # Create or update Google OAuth app
            google_app, created = SocialApp.objects.get_or_create(
                provider='google',
                defaults={
                    'name': 'Google',
                    'client_id': client_id,
                    'secret': client_secret,
                }
            )
            
            if not created:
                # Update existing app
                google_app.client_id = client_id
                google_app.secret = client_secret
                google_app.save()
                
                self.stdout.write(
                    self.style.SUCCESS('Updated Google OAuth application')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Created Google OAuth application')
                )

            # Add site to the app
            google_app.sites.add(site)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Google OAuth application configured successfully!\n'
                    f'Client ID: {client_id[:10]}...\n'
                    f'Site: {site.domain}\n'
                    f'You can now test Google OAuth at: http://{site.domain}/accounts/google/login/'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up Google OAuth: {str(e)}')
            )
