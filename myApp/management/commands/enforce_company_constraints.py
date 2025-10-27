"""
Management command to enforce NOT NULL constraints on company fields
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from myApp.models import Property, Lead, PropertyUpload
from myApp.services import CompanyService


class Command(BaseCommand):
    help = 'Enforce NOT NULL constraints on company fields'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Get default company
            company = CompanyService.get_default_company()
            
            # Update any remaining NULL company fields
            properties_updated = Property.objects.filter(company__isnull=True).update(company=company)
            leads_updated = Lead.objects.filter(company__isnull=True).update(company=company)
            uploads_updated = PropertyUpload.objects.filter(company__isnull=True).update(company=company)
            
            self.stdout.write(f'Updated {properties_updated} properties')
            self.stdout.write(f'Updated {leads_updated} leads')
            self.stdout.write(f'Updated {uploads_updated} uploads')
            
            # Note: In a real migration, you would alter the table constraints here
            # For now, we'll just ensure all records have a company
            self.stdout.write(
                self.style.SUCCESS('All records now have company assignments')
            )
