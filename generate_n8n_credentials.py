#!/usr/bin/env python
"""
Generate secure credentials for n8n integration

Usage:
    python generate_n8n_credentials.py

Output:
    N8N_TOKEN=<generated-token>
    N8N_HMAC_SECRET=<generated-secret>
"""

import secrets
import sys


def generate_credentials():
    """Generate secure random tokens for n8n integration"""
    
    # Generate N8N_TOKEN (Bearer token for authentication)
    # Using URL-safe base64 encoding, 32 bytes = 43 characters
    n8n_token = secrets.token_urlsafe(32)
    
    # Generate N8N_HMAC_SECRET (HMAC signing secret)
    # Using URL-safe base64 encoding, 32 bytes = 43 characters
    n8n_hmac_secret = secrets.token_urlsafe(32)
    
    print("=" * 60)
    print("N8N Integration Credentials")
    print("=" * 60)
    print()
    print("Add these to your Django .env file:")
    print()
    print(f"N8N_TOKEN={n8n_token}")
    print(f"N8N_HMAC_SECRET={n8n_hmac_secret}")
    print()
    print("=" * 60)
    print("Also share these values with your n8n developer")
    print("=" * 60)
    print()
    print("⚠️  SECURITY WARNING:")
    print("   - Keep these values secret")
    print("   - Don't commit to version control")
    print("   - Store in secure password manager")
    print("   - Use different values for dev/staging/production")
    print()
    
    return n8n_token, n8n_hmac_secret


if __name__ == "__main__":
    try:
        generate_credentials()
    except Exception as e:
        print(f"Error generating credentials: {e}", file=sys.stderr)
        sys.exit(1)
