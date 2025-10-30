"""
Management command to initialize the platform with default data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myApp.models import Organization, Plan, Subscription
from myApp.services_organization import OrganizationService
from django.utils import timezone


class Command(BaseCommand):
    help = 'Initialize platform with default plans and migrate existing data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--migrate-companies',
            action='store_true',
            help='Migrate existing Company records to Organization',
        )
        parser.add_argument(
            '--create-plans',
            action='store_true',
            help='Create default subscription plans',
        )

    def handle(self, *args, **options):
        if options['create_plans']:
            self.create_default_plans()
        
        if options['migrate_companies']:
            self.migrate_companies()

    def create_default_plans(self):
        """Create default subscription plans"""
        self.stdout.write('Creating default subscription plans...')
        
        plans = OrganizationService.create_default_plans()
        
        for plan in plans:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created plan: {plan.name} (${plan.monthly_usd/100:.2f}/month)')
            )

    def migrate_companies(self):
        """Migrate existing Company records to Organization"""
        from myApp.models import Company
        
        self.stdout.write('Migrating Company records to Organization...')
        
        companies = Company.objects.all()
        migrated_count = 0
        
        for company in companies:
            # Create organization from company
            organization = Organization.objects.create(
                name=company.name,
                slug=company.slug,
                logo_url=company.logo,
                brand_primary=company.brand_primary_color,
                brand_accent=company.brand_secondary_color,
                created_by=company.created_by if hasattr(company, 'created_by') else None
            )
            
            # Create trial subscription
            trial_plan = Plan.objects.filter(code='starter').first()
            if trial_plan:
                Subscription.objects.create(
                    organization=organization,
                    plan=trial_plan,
                    status='trialing',
                    current_period_end=timezone.now() + timezone.timedelta(days=14)
                )
            
            migrated_count += 1
            self.stdout.write(f'✓ Migrated: {company.name} -> {organization.name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully migrated {migrated_count} companies to organizations')
        )
