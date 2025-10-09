"""
Webhook integration for Katalyst CRM
"""
import requests
import logging
from typing import Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)

# Webhook URLs
CHAT_INQUIRY_WEBHOOK = "https://katalyst-crm.fly.dev/webhook/ca05d7c5-984c-4d95-8636-1ed3d80f5545ponse"
PROPERTY_LISTING_WEBHOOK = "https://katalyst-crm.fly.dev/webhook-test/7e36f0ef-e0b2-498d-886c-f06bef9afd80"


def send_webhook(url: str, data: Dict[str, Any]) -> bool:
    """
    Send data to a webhook URL
    
    Args:
        url: The webhook URL to send to
        data: Dictionary of data to send
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'PropertyListingBot/1.0',
            'Origin': 'https://project03-production.up.railway.app',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type'
        }
        
        response = requests.post(
            url,
            json=data,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"Webhook sent successfully to {url}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send webhook to {url}: {str(e)}")
        return False


def send_chat_inquiry_webhook(lead_data: Dict[str, Any]) -> bool:
    """
    Send chat inquiry data to Katalyst CRM
    
    Args:
        lead_data: Dictionary containing lead/inquiry information
    
    Returns:
        bool: True if successful
    """
    webhook_payload = {
        "type": "chat_inquiry",
        "timestamp": lead_data.get("timestamp"),
        "session_id": lead_data.get("session_id", ""),
        "lead": {
            "id": str(lead_data.get("id", "")),
            "name": lead_data.get("name", ""),
            "phone": lead_data.get("phone", ""),
            "email": lead_data.get("email", ""),
            "buy_or_rent": lead_data.get("buy_or_rent", ""),
            "budget_max": lead_data.get("budget_max"),
            "beds": lead_data.get("beds"),
            "areas": lead_data.get("areas", ""),
            "interest_ids": lead_data.get("interest_ids", ""),
            "message": lead_data.get("message", ""),
        },
        "tracking": {
            "utm_source": lead_data.get("utm_source", ""),
            "utm_campaign": lead_data.get("utm_campaign", ""),
            "referrer": lead_data.get("referrer", ""),
        },
        "property": lead_data.get("property", {})
    }
    
    return send_webhook(CHAT_INQUIRY_WEBHOOK, webhook_payload)


def send_property_listing_webhook(property_data: Dict[str, Any]) -> bool:
    """
    Send property listing data to Katalyst CRM
    
    Args:
        property_data: Dictionary containing property information
    
    Returns:
        bool: True if successful
    """
    webhook_payload = {
        "type": "property_listing",
        "timestamp": property_data.get("timestamp"),
        "session_id": property_data.get("session_id", ""),
        "property": {
            "id": str(property_data.get("id", "")),
            "slug": property_data.get("slug", ""),
            "title": property_data.get("title", ""),
            "description": property_data.get("description", ""),
            "price_amount": property_data.get("price_amount"),
            "city": property_data.get("city", ""),
            "area": property_data.get("area", ""),
            "beds": property_data.get("beds"),
            "baths": property_data.get("baths"),
            "floor_area_sqm": property_data.get("floor_area_sqm"),
            "parking": property_data.get("parking"),
            "hero_image": property_data.get("hero_image", ""),
            "badges": property_data.get("badges", ""),
            "created_at": property_data.get("created_at"),
        },
        "upload_info": {
            "upload_id": str(property_data.get("upload_id", "")),
            "validation_result": property_data.get("validation_result", {}),
            "missing_fields": property_data.get("missing_fields", []),
            "consolidated_information": property_data.get("consolidated_information", ""),
        },
        "source": property_data.get("source", "website")
    }
    
    return send_webhook(PROPERTY_LISTING_WEBHOOK, webhook_payload)


def send_property_chat_webhook(chat_data: Dict[str, Any]) -> bool:
    """
    Send property chat message to chat inquiry webhook
    
    Args:
        chat_data: Dictionary containing chat message information
    
    Returns:
        bool: True if successful
    """
    webhook_payload = {
        "type": "Property_inquiry",  # Updated to match n8n expectation
        "timestamp": chat_data.get("timestamp"),
        "session_id": chat_data.get("session_id", ""),
        "property": {
            "id": str(chat_data.get("property_id", "")),
            "slug": chat_data.get("property_slug", ""),
            "title": chat_data.get("property_title", ""),
            "city": chat_data.get("property_city", ""),
            "price": chat_data.get("property_price"),
        },
        "chat": {
            "message": chat_data.get("message", ""),
            "response": chat_data.get("response", ""),
            "user_agent": chat_data.get("user_agent", ""),
            "ip_address": chat_data.get("ip_address", ""),
        },
        "tracking": {
            "referrer": chat_data.get("referrer", ""),
        }
    }
    
    return send_webhook(CHAT_INQUIRY_WEBHOOK, webhook_payload)


def send_prompt_search_webhook(search_data: Dict[str, Any]) -> bool:
    """
    Send prompt-based search data to Katalyst CRM
    
    Args:
        search_data: Dictionary containing search prompt information
    
    Returns:
        bool: True if successful
    """
    webhook_payload = {
        "type": "Property_inquiry",  # Using same type as chat
        "timestamp": search_data.get("timestamp"),
        "session_id": search_data.get("session_id", ""),
        "search": {
            "prompt": search_data.get("prompt", ""),
            "results_count": search_data.get("results_count", 0),
            "search_type": "ai_prompt"
        },
        "lead": {
            "id": "prompt_search_" + str(search_data.get("session_id", "")),
            "name": "Prompt Search User",
            "phone": "",
            "email": "",
            "buy_or_rent": search_data.get("buy_or_rent", ""),
            "budget_max": search_data.get("budget_max"),
            "beds": search_data.get("beds"),
            "areas": search_data.get("areas", ""),
            "interest_ids": search_data.get("property_ids", ""),
            "message": search_data.get("prompt", "")
        },
        "tracking": {
            "utm_source": search_data.get("utm_source", ""),
            "utm_campaign": search_data.get("utm_campaign", ""),
            "referrer": search_data.get("referrer", ""),
        },
        "property": {
            "search_session": str(search_data.get("session_id", "")),
            "prompt_used": search_data.get("prompt", ""),
            "results_found": search_data.get("results_count", 0)
        }
    }
    
    return send_webhook(CHAT_INQUIRY_WEBHOOK, webhook_payload)