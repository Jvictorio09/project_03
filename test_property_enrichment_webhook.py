"""
Test script for Property Enrichment Webhook
Run: python test_property_enrichment_webhook.py
"""
import requests
import json
from datetime import datetime

# Your webhook URL
WEBHOOK_URL = "https://mindalgos-project.fly.dev/webhook-test/enrich-property"

def test_property_enrichment_webhook():
    """Test the property enrichment webhook"""
    print("\n🧪 Testing Property Enrichment Webhook...")
    print(f"URL: {WEBHOOK_URL}")
    
    # Test payload - you'll need to replace with actual property IDs from your database
    test_data = {
        "property_id": "test-property-123",  # Replace with actual property ID
        "company_id": "test-company-456",   # Replace with actual company ID
        "timestamp": datetime.now().isoformat()
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'PropertyEnrichmentBot/1.0 (Test)',
    }
    
    try:
        print(f"\n📤 Sending test payload:")
        print(json.dumps(test_data, indent=2))
        
        response = requests.post(
            WEBHOOK_URL,
            json=test_data,
            headers=headers,
            timeout=30
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Webhook responded successfully!")
            try:
                response_data = response.json()
                print(f"📥 Response Data:")
                print(json.dumps(response_data, indent=2))
            except:
                print(f"📥 Response Text: {response.text}")
        else:
            print(f"❌ ERROR: Webhook returned status {response.status_code}")
            print(f"📥 Error Response: {response.text}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ ERROR: Cannot connect to webhook URL - {str(e)}")
        print("💡 Make sure your server is running and accessible")
    except requests.exceptions.Timeout as e:
        print(f"❌ ERROR: Request timed out - {str(e)}")
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Request failed - {str(e)}")
    except Exception as e:
        print(f"❌ ERROR: Unexpected error - {str(e)}")

def test_with_real_property_id():
    """Test with a real property ID from your database"""
    print("\n🔍 To test with real data:")
    print("1. Go to your Django admin or database")
    print("2. Find a property ID from your Property model")
    print("3. Replace 'test-property-123' in the script with the real ID")
    print("4. Run the test again")
    print("\nExample:")
    print("test_data = {")
    print('    "property_id": "550e8400-e29b-41d4-a716-446655440000",  # Real UUID')
    print('    "company_id": "550e8400-e29b-41d4-a716-446655440001",  # Real UUID')
    print('    "timestamp": datetime.now().isoformat()')
    print("}")

if __name__ == "__main__":
    print("🚀 Property Enrichment Webhook Test")
    print("=" * 50)
    
    test_property_enrichment_webhook()
    test_with_real_property_id()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")
    print("\n💡 Next steps:")
    print("1. If successful, share the webhook URL with your n8n team")
    print("2. They can now pin the data and test the integration")
    print("3. Monitor your Django logs for webhook activity")

