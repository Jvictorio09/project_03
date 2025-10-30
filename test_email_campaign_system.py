#!/usr/bin/env python
"""
Test script for the email campaign system
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myProject.settings')
django.setup()

from myApp.models import EmailAccount, Campaign, CampaignStep, Lead, Organization, User
from django.utils import timezone
from datetime import timedelta

def test_email_campaign_system():
    """Test the email campaign system components"""
    print("🧪 Testing Email Campaign System...")
    
    try:
        # Test 1: Check if EmailAccount model exists
        print("\n1. Testing EmailAccount model...")
        email_account_count = EmailAccount.objects.count()
        print(f"   ✅ EmailAccount model exists ({email_account_count} records)")
        
        # Test 2: Check if Campaign model exists
        print("\n2. Testing Campaign model...")
        campaign_count = Campaign.objects.count()
        print(f"   ✅ Campaign model exists ({campaign_count} records)")
        
        # Test 3: Check if CampaignStep model exists
        print("\n3. Testing CampaignStep model...")
        campaign_step_count = CampaignStep.objects.count()
        print(f"   ✅ CampaignStep model exists ({campaign_step_count} records)")
        
        # Test 4: Check if we have organizations
        print("\n4. Testing Organization data...")
        org_count = Organization.objects.count()
        print(f"   ✅ Organizations exist ({org_count} records)")
        
        if org_count > 0:
            org = Organization.objects.first()
            print(f"   📋 Sample organization: {org.name}")
            
            # Test 5: Check email accounts for this org
            email_accounts = EmailAccount.objects.filter(organization=org)
            print(f"   📧 Email accounts for {org.name}: {email_accounts.count()}")
            
            # Test 6: Check campaigns for this org
            campaigns = Campaign.objects.filter(organization=org)
            print(f"   📬 Campaigns for {org.name}: {campaigns.count()}")
            
            # Test 7: Check leads for this org
            leads = Lead.objects.filter(organization=org)
            print(f"   👥 Leads for {org.name}: {leads.count()}")
        
        # Test 8: Test Gmail service import
        print("\n5. Testing Gmail service...")
        try:
            from myApp.services_gmail import GmailService
            gmail_service = GmailService()
            print("   ✅ GmailService imported successfully")
        except Exception as e:
            print(f"   ❌ GmailService import failed: {e}")
        
        # Test 9: Test campaign forms import
        print("\n6. Testing campaign forms...")
        try:
            from myApp.forms import CampaignForm, CampaignStepForm
            print("   ✅ Campaign forms imported successfully")
        except Exception as e:
            print(f"   ❌ Campaign forms import failed: {e}")
        
        print("\n🎉 Email Campaign System Test Complete!")
        print("\n📋 Next Steps:")
        print("   1. Go to Settings → Email Accounts")
        print("   2. Click 'Connect Gmail' to link your Gmail account")
        print("   3. Go to Campaigns → Create Campaign")
        print("   4. Add email steps and send to your leads!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_email_campaign_system()
    sys.exit(0 if success else 1)
