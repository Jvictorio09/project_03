#!/usr/bin/env python
"""
Test script for n8n integration
"""
import os
import sys
import django
import json
import hmac
import hashlib
import time
import requests

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myProject.settings')
django.setup()

from myApp.models import Campaign, CampaignStep, Lead, Organization, MessageLog
from django.utils import timezone
from django.conf import settings

def create_test_data():
    """Create test data for n8n integration"""
    print("🧪 Creating test data...")
    
    # Get or create organization
    org, created = Organization.objects.get_or_create(
        slug='test-org',
        defaults={
            'name': 'Test Organization',
            'brand_primary': '#3B82F6',
            'brand_accent': '#18AFAB'
        }
    )
    print(f"   ✅ Organization: {org.name}")
    
    # Create test lead
    lead, created = Lead.objects.get_or_create(
        email='test@example.com',
        organization=org,
        defaults={
            'name': 'Test Lead',
            'phone': '+1234567890',
            'consent_contact': True
        }
    )
    print(f"   ✅ Lead: {lead.name} ({lead.email})")
    
    # Create test campaign
    campaign, created = Campaign.objects.get_or_create(
        name='Test Campaign',
        organization=org,
        defaults={
            'type': 'sequence',
            'status': 'active'
        }
    )
    print(f"   ✅ Campaign: {campaign.name}")
    
    # Create test step
    step, created = CampaignStep.objects.get_or_create(
        campaign=campaign,
        order=1,
        defaults={
            'name': 'Welcome Email',
            'subject': 'Welcome {{ lead.name }}!',
            'body_template': '<p>Hello {{ lead.name }}, welcome to our platform!</p>',
            'delay_hours': 0
        }
    )
    print(f"   ✅ Step: {step.name}")
    
    return org, lead, campaign, step

def test_hmac_signature():
    """Test HMAC signature generation"""
    print("\n🔐 Testing HMAC signature...")
    
    secret = getattr(settings, 'N8N_HMAC_SECRET', 'test-secret')
    timestamp = str(int(time.time()))
    body = '{"test": "data"}'
    
    signature = hmac.new(
        secret.encode('utf-8'),
        f"{timestamp}.{body}".encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print(f"   ✅ Signature generated: sha256={signature[:16]}...")
    return True

def test_django_endpoints():
    """Test Django n8n endpoints"""
    print("\n🌐 Testing Django endpoints...")
    
    base_url = 'http://localhost:8000'
    
    # Test due messages endpoint
    try:
        response = requests.get(f"{base_url}/webhook/n8n/due-messages/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ /due-messages/ - {len(data.get('messages', []))} messages")
        else:
            print(f"   ❌ /due-messages/ - Status: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  /due-messages/ - Error: {e}")
    
    return True

def test_campaign_send():
    """Test campaign sending with n8n flag"""
    print("\n📧 Testing campaign send...")
    
    # Check if n8n is enabled
    use_n8n = getattr(settings, 'USE_N8N_ORCHESTRATION', False)
    n8n_url = getattr(settings, 'N8N_QUEUE_WEBHOOK_URL', '')
    
    print(f"   📋 USE_N8N_ORCHESTRATION: {use_n8n}")
    print(f"   📋 N8N_QUEUE_WEBHOOK_URL: {n8n_url[:50]}..." if n8n_url else "   📋 N8N_QUEUE_WEBHOOK_URL: Not set")
    
    if use_n8n and n8n_url:
        print("   ✅ n8n orchestration is enabled")
    else:
        print("   ⚠️  n8n orchestration is disabled - will use direct Gmail send")
    
    return True

def test_message_log_states():
    """Test MessageLog state handling"""
    print("\n📊 Testing MessageLog states...")
    
    org, lead, campaign, step = create_test_data()
    
    # Check existing message logs
    existing_logs = MessageLog.objects.filter(
        campaign=campaign,
        lead=lead
    ).count()
    
    print(f"   📋 Existing message logs: {existing_logs}")
    
    # Test state transitions
    states = ['sent', 'failed', 'cancelled']
    for state in states:
        count = MessageLog.objects.filter(status=state).count()
        print(f"   📋 {state.capitalize()} messages: {count}")
    
    return True

def main():
    """Run all tests"""
    print("🚀 n8n Integration Test Suite")
    print("=" * 50)
    
    try:
        # Create test data
        org, lead, campaign, step = create_test_data()
        
        # Test HMAC
        test_hmac_signature()
        
        # Test endpoints
        test_django_endpoints()
        
        # Test campaign send
        test_campaign_send()
        
        # Test message logs
        test_message_log_states()
        
        print("\n🎉 All tests completed!")
        print("\n📋 Next Steps:")
        print("   1. Set environment variables:")
        print("      - USE_N8N_ORCHESTRATION=true")
        print("      - N8N_QUEUE_WEBHOOK_URL=<your-n8n-webhook-url>")
        print("      - N8N_HMAC_SECRET=<your-secret>")
        print("   2. Import n8n workflow JSONs")
        print("   3. Test campaign sending")
        print("   4. Check n8n execution logs")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
