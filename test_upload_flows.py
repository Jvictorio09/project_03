#!/usr/bin/env python
"""
Test script to verify both AI and Manual upload flows work perfectly
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myProject.settings')
django.setup()

from myApp.models import Property, PropertyUpload
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
import json


def test_ai_upload_flow():
    """Test the AI upload flow"""
    print("🤖 Testing AI Upload Flow...")
    
    client = Client()
    
    # Test data
    property_description = """
    Beautiful 3-bedroom, 2-bathroom house in downtown Los Angeles. 
    Recently renovated with modern kitchen, hardwood floors, and a private backyard. 
    Located near schools and shopping centers. Asking $850,000.
    """
    
    # Create a test image file
    test_image = SimpleUploadedFile(
        "test_property.jpg",
        b"fake_image_content",
        content_type="image/jpeg"
    )
    
    # Test AI upload
    response = client.post('/ai-prompt-listing/', {
        'property_description': property_description,
        'additional_info': 'Pet-friendly neighborhood',
        'hero_image': test_image,
    })
    
    print(f"  AI Upload Response: {response.status_code}")
    
    if response.status_code == 200:
        # Check if PropertyUpload was created
        uploads = PropertyUpload.objects.filter(description__icontains="Beautiful 3-bedroom")
        if uploads.exists():
            upload = uploads.first()
            print(f"  ✅ PropertyUpload created: {upload.title}")
            print(f"  ✅ Image URL: {upload.hero_image}")
            print(f"  ✅ Status: {upload.status}")
            return upload
        else:
            print("  ❌ No PropertyUpload found")
            return None
    else:
        print(f"  ❌ AI Upload failed: {response.status_code}")
        return None


def test_manual_upload_flow():
    """Test the manual upload flow"""
    print("\n📝 Testing Manual Upload Flow...")
    
    client = Client()
    
    # Create a test image file
    test_image = SimpleUploadedFile(
        "manual_test_property.jpg",
        b"fake_manual_image_content",
        content_type="image/jpeg"
    )
    
    # Test manual upload
    response = client.post('/manual-form-listing/', {
        'title': 'Manual Test Property',
        'description': 'This is a test property uploaded manually with all details filled out.',
        'price_amount': '750000',
        'city': 'San Francisco',
        'area': 'Mission District',
        'beds': '2',
        'baths': '2',
        'property_type': 'Condo',
        'listing_status': 'For Sale',
        'street_address': '123 Test Street',
        'state': 'CA',
        'zip_code': '94110',
        'hero_image': test_image,
    })
    
    print(f"  Manual Upload Response: {response.status_code}")
    
    if response.status_code == 200:
        # Check if PropertyUpload was created
        uploads = PropertyUpload.objects.filter(title="Manual Test Property")
        if uploads.exists():
            upload = uploads.first()
            print(f"  ✅ PropertyUpload created: {upload.title}")
            print(f"  ✅ Image URL: {upload.hero_image}")
            print(f"  ✅ Status: {upload.status}")
            return upload
        else:
            print("  ❌ No PropertyUpload found")
            return None
    else:
        print(f"  ❌ Manual Upload failed: {response.status_code}")
        return None


def test_property_creation(upload):
    """Test Property creation from upload"""
    if not upload:
        return None
        
    print(f"\n🏠 Testing Property Creation from Upload: {upload.title}")
    
    try:
        from myApp.views import create_property_from_upload
        create_property_from_upload(upload)
        
        # Check if Property was created
        properties = Property.objects.filter(title=upload.title)
        if properties.exists():
            property_obj = properties.first()
            print(f"  ✅ Property created: {property_obj.title}")
            print(f"  ✅ Slug: {property_obj.slug}")
            print(f"  ✅ Image URL: {property_obj.hero_image}")
            print(f"  ✅ Price: ${property_obj.price_amount}")
            print(f"  ✅ Location: {property_obj.city}, {property_obj.area}")
            return property_obj
        else:
            print("  ❌ No Property found")
            return None
            
    except Exception as e:
        print(f"  ❌ Property creation failed: {e}")
        return None


def test_database_consistency():
    """Test database consistency"""
    print("\n🗄️ Testing Database Consistency...")
    
    # Check PropertyUpload records
    uploads = PropertyUpload.objects.all()
    print(f"  Total PropertyUploads: {uploads.count()}")
    
    for upload in uploads:
        if upload.hero_image:
            if 'res.cloudinary.com' in upload.hero_image:
                print(f"  ✅ {upload.title} - Cloudinary URL")
            else:
                print(f"  ⚠️  {upload.title} - Non-Cloudinary URL: {upload.hero_image}")
        else:
            print(f"  ❌ {upload.title} - No image")
    
    # Check Property records
    properties = Property.objects.all()
    print(f"  Total Properties: {properties.count()}")
    
    for prop in properties:
        if prop.hero_image:
            if 'res.cloudinary.com' in prop.hero_image:
                print(f"  ✅ {prop.title} - Cloudinary URL")
            else:
                print(f"  ⚠️  {prop.title} - Non-Cloudinary URL: {prop.hero_image}")
        else:
            print(f"  ❌ {prop.title} - No image")


def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    # Remove test uploads
    test_uploads = PropertyUpload.objects.filter(
        title__icontains="Test"
    )
    print(f"  Removing {test_uploads.count()} test uploads")
    test_uploads.delete()
    
    # Remove test properties
    test_properties = Property.objects.filter(
        title__icontains="Test"
    )
    print(f"  Removing {test_properties.count()} test properties")
    test_properties.delete()


if __name__ == "__main__":
    print("🚀 Testing Upload Flows...")
    
    try:
        # Test AI upload flow
        ai_upload = test_ai_upload_flow()
        
        # Test manual upload flow
        manual_upload = test_manual_upload_flow()
        
        # Test property creation
        ai_property = test_property_creation(ai_upload)
        manual_property = test_property_creation(manual_upload)
        
        # Test database consistency
        test_database_consistency()
        
        print("\n✅ Upload flow testing completed!")
        
        # Clean up
        cleanup_test_data()
        
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
