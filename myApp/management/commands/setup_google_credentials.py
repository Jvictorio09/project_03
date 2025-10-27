from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Set up Google OAuth credentials'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("🚀 Setting up Google OAuth credentials..."))
        
        # Check if credentials exist
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            self.stdout.write(self.style.WARNING(
                "❌ Google OAuth credentials not found in environment variables.\n"
                "Please follow these steps:\n\n"
                "1. Go to https://console.cloud.google.com/\n"
                "2. Create a new project or select existing one\n"
                "3. Enable Google+ API (or Google OAuth2 API)\n"
                "4. Go to 'Credentials' → 'Create Credentials' → 'OAuth 2.0 Client ID'\n"
                "5. Choose 'Web application'\n"
                "6. Add these authorized redirect URIs:\n"
                "   - http://127.0.0.1:8000/google/callback/\n"
                "   - http://localhost:8000/google/callback/\n"
                "7. Copy the Client ID and Client Secret\n"
                "8. Add them to your .env file:\n"
                "   GOOGLE_CLIENT_ID=your-client-id-here\n"
                "   GOOGLE_CLIENT_SECRET=your-client-secret-here\n\n"
                "Then run this command again."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Google OAuth credentials found!\n"
                f"Client ID: {client_id[:10]}...\n"
                f"Client Secret: {client_secret[:10]}...\n\n"
                f"🎉 You're ready to use Google OAuth!\n"
                f"Test it at: http://127.0.0.1:8000/google/login/"
            ))
