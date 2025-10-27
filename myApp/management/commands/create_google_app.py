"""
Management command to create Google OAuth application with placeholder credentials
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings


class Command(BaseCommand):
    help = 'Create Google OAuth application with placeholder credentials'

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

            # Create Google OAuth app with placeholder credentials
            google_app, created = SocialApp.objects.get_or_create(
                provider='google',
                defaults={
                    'name': 'Google',
                    'client_id': 'placeholder-client-id',
                    'secret': 'placeholder-client-secret',
                }
            )
            
            if not created:
                # Update existing app
                google_app.client_id = 'placeholder-client-id'
                google_app.secret = 'placeholder-client-secret'
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
                    f'Google OAuth application created successfully!\n'
                    f'You can now test the OAuth flow at: http://{site.domain}/accounts/google/login/\n'
                    f'Note: You need to update the credentials in Django admin with real Google OAuth credentials.'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating Google OAuth app: {str(e)}')
            )
