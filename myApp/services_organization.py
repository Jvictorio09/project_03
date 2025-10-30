"""
Organization service for managing multi-tenancy
"""
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from .models import Organization, Membership, Plan, Subscription
import uuid


class OrganizationService:
    """Service for organization management operations"""
    
    @staticmethod
    def create_organization_for_user(user, name=None, domain=None):
        """Create a new organization for a user"""
        if not name:
            # Generate name from email domain
            email_domain = user.email.split('@')[1] if '@' in user.email else 'company'
            name = f"{email_domain.title()} Real Estate"
        
        # Generate unique slug
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Create organization
        organization = Organization.objects.create(
            name=name,
            slug=slug,
            created_by=user
        )
        
        # Create owner membership
        Membership.objects.create(
            user=user,
            organization=organization,
            role='owner',
            is_active=True
        )
        
        # Create trial subscription
        trial_plan = Plan.objects.filter(code='starter').first()
        if trial_plan:
            Subscription.objects.create(
                organization=organization,
                plan=trial_plan,
                status='trialing',
                current_period_end=timezone.now() + timezone.timedelta(days=14)  # 14-day trial
            )
        
        return organization
    
    @staticmethod
    def get_user_organizations(user):
        """Get all organizations a user belongs to"""
        # Use correct reverse relation name for Membership → Organization FK
        return Organization.objects.filter(
            membership__user=user,
            membership__is_active=True
        ).distinct()
    
    @staticmethod
    def get_user_memberships(user):
        """Get all memberships for a user"""
        return Membership.objects.filter(
            user=user,
            is_active=True
        ).select_related('organization')
    
    @staticmethod
    def switch_organization(request, organization_id):
        """Switch user's active organization"""
        if not request.user.is_authenticated:
            return False
        
        try:
            organization = Organization.objects.get(id=organization_id)
            # Verify user has access
            if Membership.objects.filter(
                user=request.user,
                organization=organization,
                is_active=True
            ).exists():
                request.session['active_organization_id'] = str(organization.id)
                return True
        except Organization.DoesNotExist:
            pass
        
        return False
    
    @staticmethod
    def get_organization_from_request(request):
        """Get organization from request (session or subdomain)"""
        if not request.user.is_authenticated:
            return None
        
        # Check session
        active_org_id = request.session.get('active_organization_id')
        if active_org_id:
            try:
                org = Organization.objects.get(id=active_org_id)
                if Membership.objects.filter(
                    user=request.user,
                    organization=org,
                    is_active=True
                ).exists():
                    return org
            except Organization.DoesNotExist:
                pass
        
        # Check subdomain
        host = request.get_host()
        if '.' in host and not host.startswith('www.'):
            subdomain = host.split('.')[0]
            if subdomain not in ['app', 'www', 'api']:
                try:
                    org = Organization.objects.get(slug=subdomain)
                    if Membership.objects.filter(
                        user=request.user,
                        organization=org,
                        is_active=True
                    ).exists():
                        request.session['active_organization_id'] = str(org.id)
                        return org
                except Organization.DoesNotExist:
                    pass
        
        # Get first available organization
        membership = Membership.objects.filter(
            user=request.user,
            is_active=True
        ).first()
        
        if membership:
            request.session['active_organization_id'] = str(membership.organization.id)
            return membership.organization
        
        return None
    
    @staticmethod
    def create_default_plans():
        """Create default subscription plans"""
        plans_data = [
            {
                'code': 'starter',
                'name': 'Starter',
                'monthly_usd': 2900,  # $29.00
                'limits': {
                    'listings': 50,
                    'ai_calls': 1000,
                    'seats': 2,
                    'channels': 1
                }
            },
            {
                'code': 'pro',
                'name': 'Pro',
                'monthly_usd': 7900,  # $79.00
                'limits': {
                    'listings': 200,
                    'ai_calls': 5000,
                    'seats': 5,
                    'channels': 3
                }
            },
            {
                'code': 'enterprise',
                'name': 'Enterprise',
                'monthly_usd': 19900,  # $199.00
                'limits': {
                    'listings': 1000,
                    'ai_calls': 25000,
                    'seats': 20,
                    'channels': 10
                }
            }
        ]
        
        for plan_data in plans_data:
            plan, created = Plan.objects.get_or_create(
                code=plan_data['code'],
                defaults=plan_data
            )
            if created:
                print(f"Created plan: {plan.name}")
        
        return Plan.objects.all()
    
    @staticmethod
    def check_entitlements(organization, resource_type, amount=1):
        """Check if organization has entitlements for a resource"""
        try:
            subscription = organization.subscription
            plan = subscription.plan
            
            if resource_type in plan.limits:
                # Get current usage
                current_usage = OrganizationService.get_current_usage(organization, resource_type)
                limit = plan.limits[resource_type]
                
                return current_usage + amount <= limit
            
            return True  # No limit defined
        except Subscription.DoesNotExist:
            return False  # No subscription
    
    @staticmethod
    def get_current_usage(organization, resource_type):
        """Get current usage for a resource type"""
        from .models import Property, Lead, Event
        
        if resource_type == 'listings':
            return Property.objects.filter(organization=organization).count()
        elif resource_type == 'ai_calls':
            # Count AI-related events in the last 30 days
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            return Event.objects.filter(
                organization=organization,
                kind__in=['chat.message_agent', 'property.enriched'],
                created_at__gte=thirty_days_ago
            ).count()
        elif resource_type == 'seats':
            return Membership.objects.filter(
                organization=organization,
                is_active=True
            ).count()
        
        return 0
