#!/usr/bin/env python
"""
Quick script to fix image rendering issues and migrate to Cloudinary
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myProject.settings')
django.setup()

from myApp.models import Property, PropertyUpload
from myApp.utils.cloudinary_utils import upload_to_cloudinary
import requests
from django.core.files.base import ContentFile


def fix_existing_images():
    """Fix existing Property and PropertyUpload images"""
    print("🔧 Fixing existing images...")
    
    # Fix Property images
    properties = Property.objects.exclude(hero_image='').exclude(hero_image__isnull=True)
    print(f"📸 Found {properties.count()} properties with images")
    
    for prop in properties:
        if 'res.cloudinary.com' in prop.hero_image:
            print(f"  ✅ {prop.title} - Already Cloudinary")
            continue
        
        if prop.hero_image.startswith('/static/') or prop.hero_image.startswith('/media/'):
            print(f"  ⚠️  {prop.title} - Skipping placeholder")
            continue
        
        try:
            print(f"  🔄 Migrating {prop.title}...")
            # Download and re-upload to Cloudinary
            response = requests.get(prop.hero_image, timeout=10)
            response.raise_for_status()
            
            file_obj = ContentFile(response.content, name=f"property_{prop.id}.jpg")
            result = upload_to_cloudinary(file_obj, folder="migrated_properties")
            
            prop.hero_image = result['secure_url']
            prop.save()
            
            print(f"  ✅ {prop.title} - Migrated to Cloudinary")
            
        except Exception as e:
            print(f"  ❌ {prop.title} - Failed: {e}")
    
    # Fix PropertyUpload images
    uploads = PropertyUpload.objects.exclude(hero_image='').exclude(hero_image__isnull=True)
    print(f"📸 Found {uploads.count()} uploads with images")
    
    for upload in uploads:
        if 'res.cloudinary.com' in upload.hero_image:
            print(f"  ✅ {upload.title} - Already Cloudinary")
            continue
        
        if upload.hero_image.startswith('/static/') or upload.hero_image.startswith('/media/'):
            print(f"  ⚠️  {upload.title} - Skipping placeholder")
            continue
        
        try:
            print(f"  🔄 Migrating {upload.title}...")
            # Download and re-upload to Cloudinary
            response = requests.get(upload.hero_image, timeout=10)
            response.raise_for_status()
            
            file_obj = ContentFile(response.content, name=f"upload_{upload.id}.jpg")
            result = upload_to_cloudinary(file_obj, folder="migrated_uploads")
            
            upload.hero_image = result['secure_url']
            upload.save()
            
            print(f"  ✅ {upload.title} - Migrated to Cloudinary")
            
        except Exception as e:
            print(f"  ❌ {upload.title} - Failed: {e}")


def add_default_images():
    """Add default images for properties without images"""
    print("\n🖼️  Adding default images...")
    
    properties = Property.objects.filter(hero_image='')
    print(f"📸 Found {properties.count()} properties without images")
    
    default_image_url = "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&h=600&fit=crop&crop=center"
    
    for prop in properties:
        try:
            print(f"  🔄 Adding default image for {prop.title}...")
            
            response = requests.get(default_image_url, timeout=10)
            response.raise_for_status()
            
            file_obj = ContentFile(response.content, name=f"default_{prop.id}.jpg")
            result = upload_to_cloudinary(file_obj, folder="default_properties")
            
            prop.hero_image = result['secure_url']
            prop.save()
            
            print(f"  ✅ {prop.title} - Added default image")
            
        except Exception as e:
            print(f"  ❌ {prop.title} - Failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting image migration...")
    
    try:
        fix_existing_images()
        add_default_images()
        print("\n✅ Image migration completed!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
