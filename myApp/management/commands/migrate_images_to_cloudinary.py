import os
from django.core.management.base import BaseCommand
from django.conf import settings
from myApp.models import Property, PropertyUpload
from myApp.utils.cloudinary_utils import upload_to_cloudinary
import requests
from PIL import Image
import io
from django.core.files.base import ContentFile


class Command(BaseCommand):
    help = 'Migrate all existing images to Cloudinary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        self.stdout.write('🚀 Starting image migration to Cloudinary...')
        
        # Migrate Property model images
        self.migrate_property_images(dry_run)
        
        # Migrate PropertyUpload model images  
        self.migrate_property_upload_images(dry_run)
        
        self.stdout.write(self.style.SUCCESS('✅ Migration completed!'))

    def migrate_property_images(self, dry_run=False):
        """Migrate Property model hero_image URLs to Cloudinary"""
        self.stdout.write('\n📸 Migrating Property images...')
        
        properties = Property.objects.exclude(hero_image='').exclude(hero_image__isnull=True)
        
        for prop in properties:
            self.stdout.write(f'  Processing: {prop.title}')
            
            # Skip if already a Cloudinary URL
            if 'res.cloudinary.com' in prop.hero_image:
                self.stdout.write(f'    ✅ Already Cloudinary: {prop.hero_image[:50]}...')
                continue
            
            # Skip if it's a placeholder or broken URL
            if not prop.hero_image or prop.hero_image.startswith('/static/') or prop.hero_image.startswith('/media/'):
                self.stdout.write(f'    ⚠️  Skipping placeholder: {prop.hero_image}')
                continue
            
            try:
                if not dry_run:
                    # Download the image
                    response = requests.get(prop.hero_image, timeout=10)
                    response.raise_for_status()
                    
                    # Create a file-like object
                    image_data = response.content
                    filename = f"property_{prop.id}_{prop.slug}.jpg"
                    
                    # Create a Django file object
                    file_obj = ContentFile(image_data, name=filename)
                    
                    # Upload to Cloudinary
                    result = upload_to_cloudinary(file_obj, folder="migrated_properties")
                    
                    # Update the property
                    prop.hero_image = result['secure_url']
                    prop.save()
                    
                    self.stdout.write(f'    ✅ Migrated: {result["secure_url"][:50]}...')
                else:
                    self.stdout.write(f'    🔄 Would migrate: {prop.hero_image[:50]}...')
                    
            except Exception as e:
                self.stdout.write(f'    ❌ Failed: {str(e)}')

    def migrate_property_upload_images(self, dry_run=False):
        """Migrate PropertyUpload model hero_image URLs to Cloudinary"""
        self.stdout.write('\n📸 Migrating PropertyUpload images...')
        
        uploads = PropertyUpload.objects.exclude(hero_image='').exclude(hero_image__isnull=True)
        
        for upload in uploads:
            self.stdout.write(f'  Processing: {upload.title}')
            
            # Skip if already a Cloudinary URL
            if 'res.cloudinary.com' in upload.hero_image:
                self.stdout.write(f'    ✅ Already Cloudinary: {upload.hero_image[:50]}...')
                continue
            
            # Skip if it's a placeholder or broken URL
            if not upload.hero_image or upload.hero_image.startswith('/static/') or upload.hero_image.startswith('/media/'):
                self.stdout.write(f'    ⚠️  Skipping placeholder: {upload.hero_image}')
                continue
            
            try:
                if not dry_run:
                    # Download the image
                    response = requests.get(upload.hero_image, timeout=10)
                    response.raise_for_status()
                    
                    # Create a file-like object
                    image_data = response.content
                    filename = f"upload_{upload.id}.jpg"
                    
                    # Create a Django file object
                    file_obj = ContentFile(image_data, name=filename)
                    
                    # Upload to Cloudinary
                    result = upload_to_cloudinary(file_obj, folder="migrated_uploads")
                    
                    # Update the upload
                    upload.hero_image = result['secure_url']
                    upload.save()
                    
                    self.stdout.write(f'    ✅ Migrated: {result["secure_url"][:50]}...')
                else:
                    self.stdout.write(f'    🔄 Would migrate: {upload.hero_image[:50]}...')
                    
            except Exception as e:
                self.stdout.write(f'    ❌ Failed: {str(e)}')

    def add_default_images(self, dry_run=False):
        """Add default placeholder images for properties without images"""
        self.stdout.write('\n🖼️  Adding default images for properties without images...')
        
        properties = Property.objects.filter(hero_image='')
        default_image_url = "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&h=600&fit=crop&crop=center"
        
        for prop in properties:
            self.stdout.write(f'  Adding default image for: {prop.title}')
            
            if not dry_run:
                try:
                    # Download default image
                    response = requests.get(default_image_url, timeout=10)
                    response.raise_for_status()
                    
                    # Create a file-like object
                    image_data = response.content
                    filename = f"default_property_{prop.id}.jpg"
                    
                    # Create a Django file object
                    file_obj = ContentFile(image_data, name=filename)
                    
                    # Upload to Cloudinary
                    result = upload_to_cloudinary(file_obj, folder="default_properties")
                    
                    # Update the property
                    prop.hero_image = result['secure_url']
                    prop.save()
                    
                    self.stdout.write(f'    ✅ Added default: {result["secure_url"][:50]}...')
                    
                except Exception as e:
                    self.stdout.write(f'    ❌ Failed: {str(e)}')
            else:
                self.stdout.write(f'    🔄 Would add default image')
