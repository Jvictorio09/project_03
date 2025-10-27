"""
Management command to process outbox webhook messages
"""
from django.core.management.base import BaseCommand
from myApp.utils.webhook_service import WebhookService


class Command(BaseCommand):
    help = 'Process pending webhook messages from outbox'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of messages to process in one run'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        self.stdout.write('Processing webhook messages...')
        
        try:
            processed_count = WebhookService.process_outbox_messages()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully processed {processed_count} webhook messages')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing webhooks: {str(e)}')
            )
