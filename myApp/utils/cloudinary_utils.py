import cloudinary
import cloudinary.uploader
from django.conf import settings
from PIL import Image
import io
from django.core.files.uploadedfile import InMemoryUploadedFile

# Configure Cloudinary with settings
cloudinary.config(
    cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
    api_secret=settings.CLOUDINARY_STORAGE['API_SECRET']
)


def compress_image_if_needed(file):
    """
    Compress image if it's over 10MB limit
    Returns compressed file ready for Cloudinary upload
    """
    # Check if file is over 10MB
    if file.size <= 10 * 1024 * 1024:  # 10MB
        return file
    
    print(f"📦 Compressing large image: {file.size / (1024*1024):.1f}MB")
    
    try:
        # Open image with PIL
        image = Image.open(file)
        
        # Auto-rotate based on EXIF
        if hasattr(image, '_getexif'):
            exif = image._getexif()
            if exif is not None:
                orientation = exif.get(0x0112)
                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
        
        # Resize if too wide
        if image.width > 5000:
            ratio = 5000 / image.width
            new_height = int(image.height * ratio)
            image = image.resize((5000, new_height), Image.Resampling.LANCZOS)
            print(f"📏 Resized to: {image.width}x{image.height}")
        
        # Convert to WebP for better compression
        if image.format in ['PNG', 'TIFF']:
            print("🔄 Converting to WebP for better compression")
        
        # Compress iteratively
        quality = 82
        while quality >= 50:
            output = io.BytesIO()
            
            # Save as WebP with current quality
            if image.mode in ('RGBA', 'LA'):
                image.save(output, format='WebP', quality=quality, method=6)
            else:
                image = image.convert('RGB')
                image.save(output, format='WebP', quality=quality, method=6)
            
            output.seek(0)
            
            # Check if under 9.3MB
            if len(output.getvalue()) <= 9.3 * 1024 * 1024:
                print(f"✅ Compressed to {len(output.getvalue()) / (1024*1024):.1f}MB at quality {quality}%")
                
                # Create new file-like object
                compressed_file = InMemoryUploadedFile(
                    output,
                    None,
                    file.name.replace('.jpg', '.webp').replace('.png', '.webp'),
                    'image/webp',
                    len(output.getvalue()),
                    None
                )
                return compressed_file
            
            quality -= 10
        
        # If still too large, force smaller size
        print("⚠️ Still too large, forcing smaller dimensions")
        image = image.resize((3000, int(3000 * image.height / image.width)), Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        image.save(output, format='WebP', quality=60, method=6)
        output.seek(0)
        
        compressed_file = InMemoryUploadedFile(
            output,
            None,
            file.name.replace('.jpg', '.webp'),
            'image/webp',
            len(output.getvalue()),
            None
        )
        
        print(f"✅ Force compressed to {len(output.getvalue()) / (1024*1024):.1f}MB")
        return compressed_file
        
    except Exception as e:
        print(f"❌ Compression failed: {e}")
        return file


def upload_to_cloudinary(file, folder="property_uploads"):
    """
    Upload file directly to Cloudinary and return URLs
    """
    try:
        # Debug Cloudinary config
        print(f"🔧 Cloudinary Config:")
        print(f"   Cloud Name: {settings.CLOUDINARY_STORAGE['CLOUD_NAME']}")
        print(f"   API Key: {settings.CLOUDINARY_STORAGE['API_KEY'][:8]}..." if settings.CLOUDINARY_STORAGE['API_KEY'] else "   API Key: NOT SET")
        print(f"   API Secret: {'SET' if settings.CLOUDINARY_STORAGE['API_SECRET'] else 'NOT SET'}")
        
        # Compress if needed
        compressed_file = compress_image_if_needed(file)
        
        print(f"☁️ Uploading to Cloudinary: {compressed_file.name}")
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            compressed_file,
            folder=folder,
            resource_type="auto",
            eager=[
                {"width": 800, "height": 450, "crop": "fill", "quality": 85},
                {"width": 400, "height": 225, "crop": "fill", "quality": 80},
                {"width": 1200, "height": 675, "crop": "fill", "quality": 90},
            ],
            eager_async=True,
        )
        
        print(f"✅ Cloudinary upload successful: {result['public_id']}")
        print(f"📎 Secure URL: {result['secure_url']}")
        
        # Return URLs and metadata
        return {
            'secure_url': result['secure_url'],
            'public_id': result['public_id'],
            'width': result['width'],
            'height': result['height'],
            'format': result['format'],
            'bytes': result['bytes'],
            'eager_urls': [trans['secure_url'] for trans in result.get('eager', [])],
        }
        
    except Exception as e:
        print(f"❌ Cloudinary upload failed: {e}")
        import traceback
        traceback.print_exc()
        raise e


def generate_cloudinary_url(public_id, transformations=None):
    """
    Generate optimized delivery URLs for Cloudinary images
    """
    if not transformations:
        transformations = {
            'f': 'auto',  # auto format (WebP for modern browsers)
            'q': 'auto',  # auto quality
            'c': 'fill',
            'w': 800,
            'h': 450,
        }
    
    url = cloudinary.CloudinaryImage(public_id).build_url(**transformations)
    return url


def delete_cloudinary_image(public_id):
    """
    Delete image from Cloudinary
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        print(f"🗑️ Deleted from Cloudinary: {public_id}")
        return result
    except Exception as e:
        print(f"❌ Failed to delete from Cloudinary: {e}")
        return None
