"""
Management command to backfill existing data with default company
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from myApp.models import Company, Property, Lead, PropertyUpload
from myApp.services import CompanyService


class Command(BaseCommand):
    help = 'Backfill existing data with default company'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Get or create default company
            company = CompanyService.get_default_company()
            self.stdout.write(f'Using company: {company.name} ({company.slug})')
            
            # Backfill Properties
            properties_updated = Property.objects.filter(company__isnull=True).update(company=company)
            self.stdout.write(f'Updated {properties_updated} properties')
            
            # Backfill Leads
            leads_updated = Lead.objects.filter(company__isnull=True).update(company=company)
            self.stdout.write(f'Updated {leads_updated} leads')
            
            # Backfill PropertyUploads
            uploads_updated = PropertyUpload.objects.filter(company__isnull=True).update(company=company)
            self.stdout.write(f'Updated {uploads_updated} property uploads')
            
            self.stdout.write(
                self.style.SUCCESS('Successfully backfilled all data with default company')
            )
