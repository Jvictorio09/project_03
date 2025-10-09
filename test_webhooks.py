"""
Quick Webhook Testing Script
Run: python test_webhooks.py
"""
import requests
import json
from datetime import datetime

# Your actual webhook URLs
CHAT_INQUIRY_WEBHOOK = "https://katalyst-crm.fly.dev/webhook/ca05d7c5-984c-4d95-8636-1ed3d80f5545ponse"
PROPERTY_LISTING_WEBHOOK = "https://katalyst-crm.fly.dev/webhook-test/7e36f0ef-e0b2-498d-886c-f06bef9afd80"

def test_chat_inquiry_webhook():
    """Test the chat inquiry webhook"""
    print("\n🧪 Testing Chat Inquiry Webhook...")
    print(f"URL: {CHAT_INQUIRY_WEBHOOK}")
    
    test_data = {
        "type": "chat_inquiry",
        "timestamp": datetime.now().isoformat(),
        "session_id": "test-session-12345",
        "lead": {
            "id": "test-lead-123",
            "name": "Test User",
            "phone": "+1-555-0123",
            "email": "test@example.com",
            "buy_or_rent": "rent",
            "budget_max": 3000,
            "beds": 2,
            "areas": "Los Angeles",
            "message": "Test webhook message"
        },
        "tracking": {
            "utm_source": "test",
            "utm_campaign": "webhook-test",
            "referrer": "manual-test"
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'PropertyListingBot/1.0 (Test)',
    }
    
    try:
        print("📤 Sending request...")
        response = requests.post(
            CHAT_INQUIRY_WEBHOOK,
            json=test_data,
            headers=headers,
            timeout=10
        )
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response Time: {response.elapsed.total_seconds():.2f}s")
        print(f"✅ Response Body: {response.text[:200] if response.text else 'Empty'}...")
        
        if response.status_code in [200, 201, 202]:
            print("✅ SUCCESS: Webhook is working!")
            return True
        else:
            print(f"⚠️  WARNING: Got status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out (>10s)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ ERROR: Cannot connect to webhook URL - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_property_listing_webhook():
    """Test the property listing webhook"""
    print("\n🧪 Testing Property Listing Webhook...")
    print(f"URL: {PROPERTY_LISTING_WEBHOOK}")
    
    test_data = {
        "type": "property_listing",
        "timestamp": datetime.now().isoformat(),
        "session_id": "test-session-67890",
        "property": {
            "id": "test-property-456",
            "slug": "test-luxury-condo",
            "title": "Test Luxury Condo Downtown",
            "description": "Beautiful test property",
            "price_amount": 450000,
            "city": "Los Angeles",
            "area": "Downtown",
            "beds": 2,
            "baths": 2,
            "badges": "Test Listing"
        },
        "upload_info": {
            "upload_id": "test-upload-789",
            "validation_result": {},
            "missing_fields": []
        },
        "source": "webhook_test"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'PropertyListingBot/1.0 (Test)',
    }
    
    try:
        print("📤 Sending request...")
        response = requests.post(
            PROPERTY_LISTING_WEBHOOK,
            json=test_data,
            headers=headers,
            timeout=10
        )
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response Time: {response.elapsed.total_seconds():.2f}s")
        print(f"✅ Response Body: {response.text[:200] if response.text else 'Empty'}...")
        
        if response.status_code in [200, 201, 202]:
            print("✅ SUCCESS: Webhook is working!")
            return True
        else:
            print(f"⚠️  WARNING: Got status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out (>10s)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ ERROR: Cannot connect to webhook URL - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("🔌 WEBHOOK TESTING TOOL")
    print("=" * 70)
    
    # Test both webhooks
    chat_ok = test_chat_inquiry_webhook()
    listing_ok = test_property_listing_webhook()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Chat Inquiry Webhook:    {'✅ WORKING' if chat_ok else '❌ FAILED'}")
    print(f"Property Listing Webhook: {'✅ WORKING' if listing_ok else '❌ FAILED'}")
    print("\n💡 NOTE:")
    print("   - Even if webhooks fail, your app will continue working normally")
    print("   - Webhooks are non-blocking and logged")
    print("   - Check your CRM dashboard to verify data reception")
    print("=" * 70)

