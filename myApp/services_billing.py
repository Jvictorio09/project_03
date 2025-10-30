"""
Billing service for Stripe integration
"""
import stripe
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from .models import Organization, Plan, Subscription
import logging

logger = logging.getLogger(__name__)


class BillingService:
    """Service for handling billing and subscriptions"""
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    
    def create_checkout_session(self, organization, plan_code, success_url=None, cancel_url=None):
        """Create Stripe checkout session for subscription"""
        try:
            plan = Plan.objects.get(code=plan_code)
            
            # Create or get Stripe customer
            customer = self.get_or_create_customer(organization)
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': plan.name,
                        },
                        'unit_amount': plan.monthly_usd,
                        'recurring': {
                            'interval': 'month',
                        },
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url or f"{settings.BASE_URL}/billing/success/",
                cancel_url=cancel_url or f"{settings.BASE_URL}/billing/cancel/",
                metadata={
                    'organization_id': str(organization.id),
                    'plan_code': plan_code
                }
            )
            
            return session
            
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            raise
    
    def get_or_create_customer(self, organization):
        """Get or create Stripe customer for organization"""
        try:
            # Check if customer already exists
            if organization.subscription.customer_id:
                customer = stripe.Customer.retrieve(organization.subscription.customer_id)
                return customer
            
            # Create new customer
            customer = stripe.Customer.create(
                email=organization.created_by.email if organization.created_by else None,
                name=organization.name,
                metadata={
                    'organization_id': str(organization.id),
                    'organization_slug': organization.slug
                }
            )
            
            # Update subscription with customer ID
            organization.subscription.customer_id = customer.id
            organization.subscription.save()
            
            return customer
            
        except Exception as e:
            logger.error(f"Error getting/creating customer: {e}")
            raise
    
    def handle_webhook(self, payload, signature):
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
        except ValueError:
            logger.error("Invalid payload")
            raise
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature")
            raise
        
        # Handle different event types
        if event['type'] == 'customer.subscription.created':
            self.handle_subscription_created(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            self.handle_subscription_updated(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            self.handle_subscription_deleted(event['data']['object'])
        elif event['type'] == 'invoice.payment_succeeded':
            self.handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            self.handle_payment_failed(event['data']['object'])
        
        return event
    
    def handle_subscription_created(self, subscription):
        """Handle subscription creation"""
        try:
            customer_id = subscription['customer']
            subscription_id = subscription['id']
            
            # Find organization by customer ID
            organization = Organization.objects.get(
                subscription__customer_id=customer_id
            )
            
            # Update subscription
            org_subscription = organization.subscription
            org_subscription.status = 'active'
            org_subscription.current_period_end = timezone.datetime.fromtimestamp(
                subscription['current_period_end'], tz=timezone.utc
            )
            org_subscription.save()
            
            logger.info(f"Subscription created for organization {organization.name}")
            
        except Exception as e:
            logger.error(f"Error handling subscription created: {e}")
    
    def handle_subscription_updated(self, subscription):
        """Handle subscription updates"""
        try:
            customer_id = subscription['customer']
            
            # Find organization by customer ID
            organization = Organization.objects.get(
                subscription__customer_id=customer_id
            )
            
            # Update subscription
            org_subscription = organization.subscription
            org_subscription.status = subscription['status']
            org_subscription.current_period_end = timezone.datetime.fromtimestamp(
                subscription['current_period_end'], tz=timezone.utc
            )
            org_subscription.save()
            
            logger.info(f"Subscription updated for organization {organization.name}")
            
        except Exception as e:
            logger.error(f"Error handling subscription updated: {e}")
    
    def handle_subscription_deleted(self, subscription):
        """Handle subscription cancellation"""
        try:
            customer_id = subscription['customer']
            
            # Find organization by customer ID
            organization = Organization.objects.get(
                subscription__customer_id=customer_id
            )
            
            # Update subscription
            org_subscription = organization.subscription
            org_subscription.status = 'canceled'
            org_subscription.save()
            
            logger.info(f"Subscription canceled for organization {organization.name}")
            
        except Exception as e:
            logger.error(f"Error handling subscription deleted: {e}")
    
    def handle_payment_succeeded(self, invoice):
        """Handle successful payment"""
        try:
            customer_id = invoice['customer']
            
            # Find organization by customer ID
            organization = Organization.objects.get(
                subscription__customer_id=customer_id
            )
            
            # Update subscription status
            org_subscription = organization.subscription
            org_subscription.status = 'active'
            org_subscription.save()
            
            logger.info(f"Payment succeeded for organization {organization.name}")
            
        except Exception as e:
            logger.error(f"Error handling payment succeeded: {e}")
    
    def handle_payment_failed(self, invoice):
        """Handle failed payment"""
        try:
            customer_id = invoice['customer']
            
            # Find organization by customer ID
            organization = Organization.objects.get(
                subscription__customer_id=customer_id
            )
            
            # Update subscription status
            org_subscription = organization.subscription
            org_subscription.status = 'past_due'
            org_subscription.save()
            
            logger.info(f"Payment failed for organization {organization.name}")
            
        except Exception as e:
            logger.error(f"Error handling payment failed: {e}")
    
    def create_billing_portal_session(self, organization):
        """Create Stripe billing portal session"""
        try:
            customer = self.get_or_create_customer(organization)
            
            session = stripe.billing_portal.Session.create(
                customer=customer.id,
                return_url=f"{settings.BASE_URL}/settings/"
            )
            
            return session
            
        except Exception as e:
            logger.error(f"Error creating billing portal session: {e}")
            raise
    
    def check_entitlements(self, organization, resource_type, amount=1):
        """Check if organization has entitlements for a resource"""
        try:
            subscription = organization.subscription
            
            # Check if subscription is active
            if subscription.status not in ['active', 'trialing']:
                return False
            
            plan = subscription.plan
            
            if resource_type in plan.limits:
                # Get current usage
                current_usage = self.get_current_usage(organization, resource_type)
                limit = plan.limits[resource_type]
                
                return current_usage + amount <= limit
            
            return True  # No limit defined
            
        except Exception as e:
            logger.error(f"Error checking entitlements: {e}")
            return False
    
    def get_current_usage(self, organization, resource_type):
        """Get current usage for a resource type"""
        from .models import Property, Event, Membership
        
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
    
    def get_usage_summary(self, organization):
        """Get usage summary for organization"""
        try:
            subscription = organization.subscription
            plan = subscription.plan
            
            usage = {}
            for resource_type, limit in plan.limits.items():
                current = self.get_current_usage(organization, resource_type)
                usage[resource_type] = {
                    'current': current,
                    'limit': limit,
                    'percentage': (current / limit * 100) if limit > 0 else 0
                }
            
            return usage
            
        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            return {}


# Global instance
billing_service = BillingService()
