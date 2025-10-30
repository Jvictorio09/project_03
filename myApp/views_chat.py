"""
Public ChatURL and embeddable widget views
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings
import json
import openai
import uuid
import re

from .models import Organization, Lead, Event, PropertyEmbedding, Property
from .services_organization import OrganizationService


def public_chat(request, org_slug):
    """Public chat interface for organization"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Check if organization has active subscription
    try:
        subscription = organization.subscription
        if subscription.status not in ['active', 'trialing']:
            return render(request, 'chat/unavailable.html', {
                'organization': organization,
                'message': 'Chat service is currently unavailable.'
            })
    except Subscription.DoesNotExist:
        return render(request, 'chat/unavailable.html', {
            'organization': organization,
            'message': 'Chat service is currently unavailable.'
        })
    
    # Get or create session lead
    session_id = request.session.get('chat_session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        request.session['chat_session_id'] = session_id
    
    # Check if this is an embedded widget
    is_embedded = request.GET.get('embed') == '1'
    
    context = {
        'organization': organization,
        'session_id': session_id,
        'is_embedded': is_embedded,
        'chat_url': f'/chat/{org_slug}',
        'api_url': f'/api/chat/ask?org={organization.id}',
    }
    
    if is_embedded:
        return render(request, 'chat/embedded.html', context)
    else:
        return render(request, 'chat/public.html', context)


@csrf_exempt
@require_POST
def chat_api_ask(request):
    """API endpoint for chat messages"""
    try:
        org_id = request.GET.get('org')
        message = request.POST.get('message', '').strip()
        session_id = request.POST.get('session_id', '')
        
        if not org_id or not message:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        organization = get_object_or_404(Organization, id=org_id)
        
        # Check subscription status
        try:
            subscription = organization.subscription
            if subscription.status not in ['active', 'trialing']:
                return JsonResponse({'error': 'Service unavailable'}, status=503)
        except Subscription.DoesNotExist:
            return JsonResponse({'error': 'Service unavailable'}, status=503)
        
        # Log user message event
        Event.objects.create(
            organization=organization,
            kind='chat.message_user',
            meta={'message': message, 'session_id': session_id}
        )
        
        # Get or create lead
        lead = get_or_create_lead_from_session(organization, session_id, message)
        
        # Generate AI response
        response = generate_ai_response(organization, message, lead)
        
        # Log agent response event
        Event.objects.create(
            organization=organization,
            kind='chat.message_agent',
            meta={'response': response, 'session_id': session_id}
        )
        
        return JsonResponse({
            'response': response,
            'session_id': session_id,
            'lead_id': str(lead.id) if lead else None
        })
        
    except Exception as e:
        return JsonResponse({'error': 'Internal server error'}, status=500)


def embed_widget_js(request, org_slug):
    """JavaScript snippet for embeddable widget"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Check subscription
    try:
        subscription = organization.subscription
        if subscription.status not in ['active', 'trialing']:
            return HttpResponse('// Chat widget unavailable', content_type='application/javascript')
    except Subscription.DoesNotExist:
        return HttpResponse('// Chat widget unavailable', content_type='application/javascript')
    
    widget_config = {
        'org_slug': org_slug,
        'chat_url': f'/chat/{org_slug}',
        'api_url': f'/api/chat/ask?org={organization.id}',
        'brand_primary': organization.brand_primary,
        'brand_accent': organization.brand_accent,
        'greeting': organization.chat_greeting
    }
    
    js_content = f"""
(function() {{
    var config = {json.dumps(widget_config)};
    
    // Create widget container
    var widget = document.createElement('div');
    widget.id = 'katek-chat-widget';
    widget.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 350px;
        height: 500px;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        background: white;
        z-index: 9999;
        display: none;
    `;
    
    // Create iframe
    var iframe = document.createElement('iframe');
    iframe.src = config.chat_url + '?embed=1';
    iframe.style.cssText = `
        width: 100%;
        height: 100%;
        border: none;
        border-radius: 12px;
    `;
    
    widget.appendChild(iframe);
    
    // Create toggle button
    var toggleBtn = document.createElement('button');
    toggleBtn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: ${config.brand_primary};
        color: white;
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
    `;
    toggleBtn.innerHTML = '💬';
    
    // Toggle functionality
    toggleBtn.addEventListener('click', function() {{
        if (widget.style.display === 'none') {{
            widget.style.display = 'block';
            toggleBtn.style.display = 'none';
        }} else {{
            widget.style.display = 'none';
            toggleBtn.style.display = 'flex';
        }}
    }});
    
    // Close button
    var closeBtn = document.createElement('button');
    closeBtn.innerHTML = '×';
    closeBtn.style.cssText = `
        position: absolute;
        top: 10px;
        right: 10px;
        background: none;
        border: none;
        font-size: 20px;
        cursor: pointer;
        color: #666;
    `;
    
    closeBtn.addEventListener('click', function() {{
        widget.style.display = 'none';
        toggleBtn.style.display = 'flex';
    }});
    
    widget.appendChild(closeBtn);
    
    // Add to page
    document.body.appendChild(widget);
    document.body.appendChild(toggleBtn);
}})();
"""
    
    return HttpResponse(js_content, content_type='application/javascript')


def get_or_create_lead_from_session(organization, session_id, message):
    """Get or create lead from chat session"""
    # Try to extract contact info from message
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{{2,}}\b', message)
    phone_match = re.search(r'\b\d{{3}}[-.]?\d{{3}}[-.]?\d{{4}}\b', message)
    
    # Look for existing lead with this session
    lead = Lead.objects.filter(
        organization=organization,
        conversation_id=session_id
    ).first()
    
    if not lead:
        # Create new lead
        lead = Lead.objects.create(
            organization=organization,
            name='Chat User',
            phone=phone_match.group() if phone_match else '',
            email=email_match.group() if email_match else '',
            source='chat',
            conversation_id=session_id,
            attributes={'initial_message': message}
        )
        
        # Log lead creation event
        Event.objects.create(
            organization=organization,
            kind='lead.created',
            meta={'lead_id': str(lead.id), 'source': 'chat'}
        )
    
    return lead


def generate_ai_response(organization, message, lead):
    """Generate AI response using organization's persona and property data"""
    try:
        # Get relevant properties using vector search
        relevant_properties = search_properties_by_message(organization, message)
        
        # Build context from properties
        context = build_property_context(relevant_properties)
        
        # Build persona prompt
        persona_prompt = build_persona_prompt(organization, context)
        
        # Generate response using OpenAI
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": persona_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"I'm sorry, I'm having trouble processing your request right now. Please try again later."


def search_properties_by_message(organization, message):
    """Search for relevant properties using vector similarity"""
    try:
        # Generate embedding for the message
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        embedding_response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=message
        )
        
        query_embedding = embedding_response.data[0].embedding
        
        # For now, return active properties (vector search will be implemented with pgvector)
        return Property.objects.filter(
            organization=organization,
            is_active=True
        )[:5]
        
    except Exception as e:
        return Property.objects.filter(
            organization=organization,
            is_active=True
        )[:5]


def build_property_context(properties):
    """Build context string from properties"""
    if not properties:
        return "No properties are currently available."
    
    context_parts = []
    for prop in properties:
        context_parts.append(f"""
Property: {prop.title}
Location: {prop.city}, {prop.area}
Price: ${prop.price_amount:,}
Details: {prop.beds} bed, {prop.baths} bath, {prop.floor_area_sqm} sqm
Description: {prop.description[:200]}...
        """.strip())
    
    return "\n\n".join(context_parts)


def build_persona_prompt(organization, context):
    """Build system prompt with organization persona"""
    persona_map = {
        'friendly_consultant': 'You are a friendly and approachable real estate consultant',
        'luxury_expert': 'You are a sophisticated luxury real estate expert',
        'investor_advisor': 'You are a knowledgeable real estate investment advisor'
    }
    
    persona = persona_map.get(organization.agent_persona, persona_map['friendly_consultant'])
    
    return f"""
You are {organization.name}'s AI real estate advisor. 

Persona: {persona}
Formality Level: {organization.tone_formality}/100
Warmth Level: {organization.tone_warmth}/100
Assertiveness Level: {organization.tone_assertiveness}/100

Available Properties:
{context}

Instructions:
- Answer only from the provided property context
- If uncertain about details, ask clarifying questions
- Never invent prices or features not present in context
- Offer to collect contact information when appropriate
- Be helpful and professional
- Keep responses concise and relevant

Default greeting: "{organization.chat_greeting}"
"""
