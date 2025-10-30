"""
Test the complete Property Enrichment Flow
Run: python test_property_enrichment_flow.py
"""
import requests
import json
from datetime import datetime

def test_complete_flow():
    """Test the complete property enrichment flow"""
    print("🚀 Testing Complete Property Enrichment Flow")
    print("=" * 60)
    
    # Step 1: Test the webhook endpoint (what n8n will call)
    print("\n1️⃣ Testing Property Data Retrieval Webhook...")
    webhook_url = "https://mindalgos-project.fly.dev/webhook-test/enrich-property"
    
    test_payload = {
        "property_id": "test-property-123",  # Replace with real property ID
        "company_id": "test-company-456",   # Replace with real company ID
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(webhook_url, json=test_payload, timeout=30)
        print(f"✅ Webhook Response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Property Data Retrieved: {data.get('status')}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Webhook Error: {e}")
    
    # Step 2: Test the callback endpoint (what n8n will call back)
    print("\n2️⃣ Testing Property Enrichment Callback...")
    callback_url = "https://mindalgos-project.fly.dev/webhook/n8n/property-enrichment/"
    
    enriched_data = {
        "property_id": "test-property-123",  # Replace with real property ID
        "enrichment_data": {
            "narrative": "This modern 2BR condo offers excellent value in the heart of BGC. With proximity to major offices and shopping centers, it's perfect for young professionals seeking convenience and luxury.",
            "estimate": 5200000,
            "neighborhood_avg": 4800000,
            "source": "rentcast",
            "market_trends": {
                "appreciation_rate": 8.5,
                "days_on_market": 45,
                "comparable_sales": 12
            }
        }
    }
    
    try:
        response = requests.post(callback_url, json=enriched_data, timeout=30)
        print(f"✅ Callback Response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Property Enriched: {data.get('status')}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Callback Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Flow Test Completed!")
    
    print("\n💡 Next Steps:")
    print("1. Replace 'test-property-123' with real property IDs from your database")
    print("2. Your n8n team can now:")
    print("   - Call the webhook to get property data")
    print("   - Process and enrich the data")
    print("   - Call back with enriched data")
    print("3. Monitor your Django logs for webhook activity")

def show_system_flow():
    """Show how the system flow works"""
    print("\n🔄 YOUR SYSTEM FLOW:")
    print("=" * 40)
    print("1. User uploads property → AI validation → Property created")
    print("2. Property created → Triggers enrichment webhook to n8n")
    print("3. n8n gets property data → Enriches it → Calls back")
    print("4. Your system updates property with enriched data")
    print("5. Property now has: narrative, estimate, neighborhood_avg, etc.")
    
    print("\n📊 PROPERTY MODEL FIELDS:")
    print("=" * 30)
    print("✅ narrative - AI-generated property analysis")
    print("✅ estimate - Market value estimate") 
    print("✅ neighborhood_avg - Neighborhood average price")
    print("✅ last_updated - Last enrichment update")
    print("✅ source - Data source (rentcast, etc.)")

if __name__ == "__main__":
    test_complete_flow()
    show_system_flow()

