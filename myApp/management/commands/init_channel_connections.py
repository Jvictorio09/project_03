"""
Management command to initialize channel connections for existing organizations
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from myApp.models import Organization, ChannelConnection


class Command(BaseCommand):
    help = 'Initialize channel connections for all organizations (sets chat as connected)'

    def handle(self, *args, **options):
        organizations = Organization.objects.all()
        
        if not organizations.exists():
            self.stdout.write(self.style.WARNING('No organizations found'))
            return
        
        created_count = 0
        updated_count = 0
        
        for org in organizations:
            # Chat channel defaults to connected
            conn, created = ChannelConnection.objects.get_or_create(
                organization=org,
                channel='chat',
                defaults={
                    'status': 'connected',
                    'connected_at': timezone.now()
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created chat connection for {org.name}'))
            else:
                # Ensure chat is connected if it exists but isn't
                if conn.status != 'connected':
                    conn.status = 'connected'
                    conn.connected_at = timezone.now()
                    conn.save()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Updated chat connection for {org.name}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nSummary: {created_count} created, {updated_count} updated'
        ))

