#!/usr/bin/env python3
"""
Environment Setup Helper Script
Helps configure API keys for the KaTek Property Hub application
"""

import os
from pathlib import Path

def create_env_file():
    """Create .env file with user input"""
    print("=" * 70)
    print("🔑 KaTek Property Hub API Configuration Setup")
    print("=" * 70)
    print()
    
    env_file = Path(".env")
    
    if env_file.exists():
        response = input("⚠️  .env file already exists. Overwrite? (y/n): ").lower()
        if response != 'y':
            print("Cancelled. Exiting...")
            return
    
    print("\n📝 Let's configure your API keys...\n")
    
    # OpenAI
    print("1️⃣  OpenAI API Key (Required for AI features)")
    print("   Get it from: https://platform.openai.com/api-keys")
    openai_key = input("   Enter your OpenAI API key (or press Enter to skip): ").strip()
    if not openai_key:
        openai_key = "your-openai-api-key-here"
        print("   ⚠️  Skipped - AI features will not work until configured")
    
    print()
    
    # Cloudinary
    print("2️⃣  Cloudinary Configuration (Required for image uploads)")
    print("   Sign up at: https://cloudinary.com/users/register/free")
    print("   Get credentials from: https://console.cloudinary.com/")
    cloud_name = input("   Cloud Name: ").strip()
    api_key = input("   API Key: ").strip()
    api_secret = input("   API Secret: ").strip()
    
    if not all([cloud_name, api_key, api_secret]):
        cloud_name = cloud_name or "your-cloudinary-cloud-name"
        api_key = api_key or "your-cloudinary-api-key"
        api_secret = api_secret or "your-cloudinary-api-secret"
        print("   ⚠️  Incomplete - Image uploads will not work until configured")
    
    print()
    
    # Create .env content
    env_content = f"""# ============================================================================
# KaTek Property Hub API Configuration
# Generated automatically - DO NOT commit this file to version control
# ============================================================================

# OpenAI Configuration (Required for AI features)
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY={openai_key}

# Cloudinary Configuration (Required for image uploads)
# Get credentials from: https://console.cloudinary.com/
CLOUDINARY_CLOUD_NAME={cloud_name}
CLOUDINARY_API_KEY={api_key}
CLOUDINARY_API_SECRET={api_secret}

# Django Configuration
SECRET_KEY=django-insecure-your-secret-key-here-change-in-production
DEBUG=True
"""
    
    # Write to .env
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created successfully!")
    print()
    print("📋 Next Steps:")
    print("   1. Restart your Django server (Ctrl+C, then 'python manage.py runserver')")
    print("   2. Test image upload and AI features")
    print()
    
    # Verify configuration
    print("🔍 Verifying configuration...")
    verify_env()

def verify_env():
    """Verify environment variables are loaded"""
    from dotenv import load_dotenv
    load_dotenv()
    
    openai_key = os.getenv('OPENAI_API_KEY', '')
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME', '')
    cloud_key = os.getenv('CLOUDINARY_API_KEY', '')
    cloud_secret = os.getenv('CLOUDINARY_API_SECRET', '')
    
    print()
    status = []
    
    if openai_key and openai_key != 'your-openai-api-key-here':
        print(f"   ✅ OpenAI API Key: {openai_key[:20]}...")
        status.append(True)
    else:
        print(f"   ❌ OpenAI API Key: NOT CONFIGURED")
        status.append(False)
    
    if cloud_name and cloud_name != 'your-cloudinary-cloud-name':
        print(f"   ✅ Cloudinary Cloud Name: {cloud_name}")
        status.append(True)
    else:
        print(f"   ❌ Cloudinary Cloud Name: NOT CONFIGURED")
        status.append(False)
    
    if cloud_key and cloud_key != 'your-cloudinary-api-key':
        print(f"   ✅ Cloudinary API Key: {cloud_key[:10]}...")
        status.append(True)
    else:
        print(f"   ❌ Cloudinary API Key: NOT CONFIGURED")
        status.append(False)
    
    if cloud_secret and cloud_secret != 'your-cloudinary-api-secret':
        print(f"   ✅ Cloudinary API Secret: {'*' * 10}...")
        status.append(True)
    else:
        print(f"   ❌ Cloudinary API Secret: NOT CONFIGURED")
        status.append(False)
    
    print()
    if all(status):
        print("🎉 All API keys configured successfully!")
    else:
        print("⚠️  Some API keys are missing. The app may not work fully.")
        print("   Run this script again to update configuration.")
    print()

if __name__ == "__main__":
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

