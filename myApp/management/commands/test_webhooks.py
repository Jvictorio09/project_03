"""
Django management command to test webhooks
Usage: python manage.py test_webhooks
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from myApp.webhook import (
    send_chat_inquiry_webhook,
    send_property_listing_webhook,
    send_property_chat_webhook,
    send_prompt_search_webhook
)


class Command(BaseCommand):
    help = 'Test all webhook endpoints'

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS('🔌 WEBHOOK TESTING TOOL'))
        self.stdout.write("=" * 70)
        
        results = []
        
        # Test 1: Chat Inquiry Webhook
        self.stdout.write("\n1️⃣  Testing Chat Inquiry Webhook...")
        chat_data = {
            "id": "test-123",
            "name": "Test User",
            "phone": "+1-555-0100",
            "email": "test@example.com",
            "buy_or_rent": "rent",
            "budget_max": 3000,
            "beds": 2,
            "areas": "Los Angeles",
            "interest_ids": "",
            "utm_source": "test",
            "utm_campaign": "webhook-test",
            "referrer": "manual",
            "session_id": "test-session",
            "timestamp": timezone.now().isoformat(),
            "message": "Test webhook from Django command"
        }
        
        result = send_chat_inquiry_webhook(chat_data)
        results.append(('Chat Inquiry', result))
        if result:
            self.stdout.write(self.style.SUCCESS('   ✅ SUCCESS'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ FAILED'))
        
        # Test 2: Property Listing Webhook
        self.stdout.write("\n2️⃣  Testing Property Listing Webhook...")
        property_data = {
            "id": "test-property-456",
            "slug": "test-condo",
            "title": "Test Luxury Condo",
            "description": "Test description",
            "price_amount": 450000,
            "city": "Los Angeles",
            "area": "Downtown",
            "beds": 2,
            "baths": 2,
            "floor_area_sqm": 100,
            "parking": True,
            "hero_image": "https://example.com/image.jpg",
            "badges": "Test",
            "created_at": timezone.now().isoformat(),
            "upload_id": "test-upload-789",
            "validation_result": {},
            "missing_fields": [],
            "consolidated_information": "Test",
            "session_id": "test-session",
            "timestamp": timezone.now().isoformat(),
            "source": "test"
        }
        
        result = send_property_listing_webhook(property_data)
        results.append(('Property Listing', result))
        if result:
            self.stdout.write(self.style.SUCCESS('   ✅ SUCCESS'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ FAILED'))
        
        # Test 3: Property Chat Webhook
        self.stdout.write("\n3️⃣  Testing Property Chat Webhook...")
        chat_webhook_data = {
            "property_id": "test-prop-123",
            "property_slug": "test-property",
            "property_title": "Test Property",
            "property_city": "Los Angeles",
            "property_price": 3500,
            "message": "How much is rent?",
            "response": "The monthly rent is $3,500 USD.",
            "session_id": "test-session",
            "timestamp": timezone.now().isoformat(),
            "user_agent": "Test Agent",
            "ip_address": "127.0.0.1",
            "referrer": "http://localhost:8000/"
        }
        
        result = send_property_chat_webhook(chat_webhook_data)
        results.append(('Property Chat', result))
        if result:
            self.stdout.write(self.style.SUCCESS('   ✅ SUCCESS'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ FAILED'))
        
        # Test 4: Prompt Search Webhook
        self.stdout.write("\n4️⃣  Testing Prompt Search Webhook...")
        search_data = {
            "prompt": "2 bedroom in LA under $3000",
            "results_count": 5,
            "session_id": "test-session",
            "buy_or_rent": "rent",
            "budget_max": 3000,
            "beds": 2,
            "areas": "Los Angeles",
            "property_ids": "id1,id2,id3",
            "timestamp": timezone.now().isoformat(),
            "utm_source": "test",
            "utm_campaign": "test",
            "referrer": "http://localhost:8000/"
        }
        
        result = send_prompt_search_webhook(search_data)
        results.append(('Prompt Search', result))
        if result:
            self.stdout.write(self.style.SUCCESS('   ✅ SUCCESS'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ FAILED'))
        
        # Summary
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS('📊 SUMMARY'))
        self.stdout.write("=" * 70)
        
        for name, status in results:
            status_str = '✅ WORKING' if status else '❌ FAILED'
            if status:
                self.stdout.write(self.style.SUCCESS(f"{name:25} {status_str}"))
            else:
                self.stdout.write(self.style.ERROR(f"{name:25} {status_str}"))
        
        success_count = sum(1 for _, status in results if status)
        total_count = len(results)
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(f"Results: {success_count}/{total_count} webhooks working")
        
        if success_count == total_count:
            self.stdout.write(self.style.SUCCESS('\n✅ All webhooks are working!'))
        elif success_count > 0:
            self.stdout.write(self.style.WARNING(f'\n⚠️  {total_count - success_count} webhook(s) failed'))
        else:
            self.stdout.write(self.style.ERROR('\n❌ All webhooks failed'))
        
        self.stdout.write("\n💡 NOTE:")
        self.stdout.write("   - Check your CRM dashboard to verify data received")
        self.stdout.write("   - Failed webhooks are normal - your app continues working")
        self.stdout.write("   - Webhooks are logged but non-blocking")
        self.stdout.write("=" * 70)

