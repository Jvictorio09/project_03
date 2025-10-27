from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os

class Command(BaseCommand):
    help = 'Set up Google OAuth with real credentials from environment variables'

    def handle(self, *args, **kwargs):
        site = Site.objects.get_current()
        self.stdout.write(f"Using site: {site.domain}")

        # Get credentials from environment variables
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

        if not client_id or not client_secret:
            self.stdout.write(self.style.ERROR(
                "Google OAuth credentials not found in environment variables.\n"
                "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file.\n"
                "Get these from Google Cloud Console:\n"
                "1. Go to https://console.cloud.google.com/\n"
                "2. Create a project\n"
                "3. Enable Google+ API\n"
                "4. Create OAuth 2.0 credentials\n"
                "5. Add authorized redirect URI: http://127.0.0.1:8000/accounts/google/login/callback/\n"
                "6. Copy Client ID and Client Secret to your .env file"
            ))
            return

        # Create or update the Google OAuth app
        app, created = SocialApp.objects.get_or_create(
            provider='google',
            name='Google',
            defaults={
                'client_id': client_id,
                'secret': client_secret,
                'key': '',
            }
        )
        
        if not created:
            app.client_id = client_id
            app.secret = client_secret
            app.save()

        # Add the app to the current site
        app.sites.add(site)

        if created:
            self.stdout.write(self.style.SUCCESS("Created Google OAuth application"))
        else:
            self.stdout.write(self.style.SUCCESS("Updated Google OAuth application"))

        self.stdout.write(self.style.SUCCESS("Google OAuth setup complete!"))
        self.stdout.write(self.style.WARNING(
            "Make sure to add this redirect URI in Google Cloud Console:\n"
            f"http://{site.domain}/accounts/google/login/callback/"
        ))
