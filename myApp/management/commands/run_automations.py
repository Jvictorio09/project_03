"""
Management command to run background automation tasks
"""
from django.core.management.base import BaseCommand
from myApp.tasks import process_email_sequences, process_webhook_outbox


class Command(BaseCommand):
    help = 'Run background automation tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            choices=['email', 'webhooks', 'all'],
            default='all',
            help='Which task to run',
        )

    def handle(self, *args, **options):
        task = options['task']
        
        if task == 'email' or task == 'all':
            self.stdout.write('Processing email sequences...')
            try:
                result = process_email_sequences()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Processed {result} email sequence steps')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error processing emails: {e}')
                )
        
        if task == 'webhooks' or task == 'all':
            self.stdout.write('Processing webhook outbox...')
            try:
                process_webhook_outbox()
                self.stdout.write(
                    self.style.SUCCESS('✓ Webhook outbox processed')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error processing webhooks: {e}')
                )
