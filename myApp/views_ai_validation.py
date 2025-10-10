"""
AI-powered property validation chatbot views
Uses OpenAI to validate property descriptions and guide users through missing details
"""
import os
import json
import requests
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Property

# OpenAI API configuration from Replit AI Integrations
OPENAI_API_KEY = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")


def call_openai(messages, temperature=0.7):
    """Call OpenAI API using requests"""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": temperature
    }
    
    response = requests.post(
        f"{OPENAI_BASE_URL}/chat/completions",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")

# Load system prompt
SYSTEM_PROMPT_PATH = "attached_assets/property_validation_system_prompt.txt"
with open(SYSTEM_PROMPT_PATH, 'r') as f:
    SYSTEM_PROMPT = f.read()


def init_ai_validation_chat(request: HttpRequest) -> HttpResponse:
    """
    Initialize AI validation chat when user submits property description + photo
    Sends description to OpenAI for validation check
    """
    if request.method == 'POST':
        property_description = request.POST.get('property_description', '').strip()
        hero_image = request.FILES.get('hero_image')
        
        if not property_description:
            return HttpResponse("Property description is required", status=400)
        
        # Store in session
        if not request.session.session_key:
            request.session.create()
        
        # Initialize session data
        request.session['validation_chat_history'] = []
        request.session['property_description'] = property_description
        request.session['property_image_url'] = None
        request.session['listing_complete'] = False
        
        # Handle image upload if provided
        if hero_image:
            try:
                from .utils.cloudinary_utils import upload_to_cloudinary
                cloudinary_result = upload_to_cloudinary(hero_image, folder="ai_validation")
                request.session['property_image_url'] = cloudinary_result['secure_url']
            except Exception as e:
                print(f"Image upload error: {e}")
        
        # Send initial message to OpenAI
        try:
            ai_response = call_openai([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": property_description}
            ])
            
            # Store conversation
            request.session['validation_chat_history'].append({
                "role": "user",
                "message": property_description,
                "timestamp": timezone.now().isoformat()
            })
            request.session['validation_chat_history'].append({
                "role": "assistant",
                "message": ai_response,
                "timestamp": timezone.now().isoformat()
            })
            request.session.modified = True
            
            # Check if complete
            if "Ready to add listing" in ai_response or "✅ Ready to add listing" in ai_response:
                request.session['listing_complete'] = True
                request.session.modified = True
            
            # Render chatbox interface
            return render(request, 'partials/ai_validation_chatbox.html', {
                'initial_message': property_description,
                'ai_response': ai_response,
                'listing_complete': request.session.get('listing_complete', False)
            })
            
        except Exception as e:
            print(f"OpenAI error: {e}")
            return HttpResponse(f"Error: {str(e)}", status=500)
    
    return HttpResponse("Method not allowed", status=405)


@require_POST
def ai_validation_chat(request: HttpRequest) -> HttpResponse:
    """
    Handle ongoing AI validation conversation
    Sends user responses to OpenAI and returns AI questions/confirmations
    """
    user_message = request.POST.get('message', '').strip()
    
    if not user_message:
        return JsonResponse({"error": "Message required"}, status=400)
    
    # Get conversation history
    chat_history = request.session.get('validation_chat_history', [])
    
    # Build messages for OpenAI
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    for msg in chat_history:
        messages.append({
            "role": msg["role"],
            "content": msg["message"]
        })
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        ai_response = call_openai(messages)
        
        # Update chat history
        chat_history.append({
            "role": "user",
            "message": user_message,
            "timestamp": timezone.now().isoformat()
        })
        chat_history.append({
            "role": "assistant",
            "message": ai_response,
            "timestamp": timezone.now().isoformat()
        })
        
        request.session['validation_chat_history'] = chat_history
        
        # Check if listing is complete
        listing_complete = False
        if "Ready to add listing" in ai_response or "✅ Ready to add listing" in ai_response:
            listing_complete = True
            request.session['listing_complete'] = True
            
            # Auto-save property to database
            try:
                from django.utils.text import slugify
                property_data = extract_property_data_from_conversation(chat_history)
                
                # Generate unique slug
                title = property_data.get('title', 'New Property')
                base_slug = slugify(title)
                slug = base_slug
                counter = 1
                while Property.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                # Create property
                property = Property.objects.create(
                    slug=slug,
                    title=title,
                    description=property_data.get('description', ''),
                    price_amount=property_data.get('price', 0),
                    city=property_data.get('city', ''),
                    area=property_data.get('area', ''),
                    beds=property_data.get('beds', 1),
                    baths=property_data.get('baths', 1),
                    hero_image=request.session.get('property_image_url', ''),
                    badges=property_data.get('badges', ''),
                    floor_area_sqm=property_data.get('floor_area', 0)
                )
                
                request.session['saved_property_id'] = property.slug
                print(f"✅ Property saved with slug: {property.slug}")
                
            except Exception as e:
                print(f"Error saving property: {e}")
        
        request.session.modified = True
        
        # Return response for HTMX
        if request.headers.get('HX-Request'):
            return render(request, "partials/ai_validation_message.html", {
                "message": ai_response,
                "role": "assistant",
                "timestamp": timezone.now(),
                "listing_complete": listing_complete,
                "property_id": request.session.get('saved_property_id')
            })
        
        return JsonResponse({
            "response": ai_response,
            "listing_complete": listing_complete
        })
        
    except Exception as e:
        print(f"OpenAI error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


def extract_property_data_from_conversation(chat_history):
    """
    Extract property data from the conversation history
    Uses OpenAI to parse the final complete property details
    """
    # Combine all messages
    full_conversation = "\n".join([
        f"{msg['role']}: {msg['message']}" 
        for msg in chat_history
    ])
    
    extraction_prompt = f"""Based on this conversation, extract the property details in JSON format:

{full_conversation}

Return a JSON object with these fields (use reasonable defaults if not specified):
{{
    "title": "property title",
    "description": "full property description",
    "price": 1000000,
    "city": "city name",
    "area": "area/neighborhood",
    "beds": 3,
    "baths": 2,
    "property_type": "house/condo/etc",
    "badges": "comma,separated,features",
    "floor_area": 100
}}

Return ONLY the JSON, no other text."""
    
    try:
        json_str = call_openai([
            {"role": "user", "content": extraction_prompt}
        ], temperature=0.3).strip()
        # Remove markdown code blocks if present
        if json_str.startswith('```'):
            json_str = json_str.split('```')[1]
            if json_str.startswith('json'):
                json_str = json_str[4:]
        json_str = json_str.strip()
        
        return json.loads(json_str)
    except Exception as e:
        print(f"Extraction error: {e}")
        # Return defaults
        return {
            "title": "New Property",
            "description": full_conversation[:500],
            "price": 0,
            "city": "",
            "area": "",
            "beds": 1,
            "baths": 1,
            "property_type": "house",
            "badges": "",
            "floor_area": None
        }
