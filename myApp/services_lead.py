"""
Lead capture and webhook service
"""
import json
import hmac
import hashlib
import requests
import re
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Lead, WebhookOutbox, Event, Organization, LeadMessage, LeadPropertyLink, Property
from .services_vector import vector_service
import uuid
import logging

logger = logging.getLogger(__name__)


class LeadCaptureService:
    """Service for capturing and processing leads"""
    
    def __init__(self):
        self.webhook_secret = settings.WEBHOOK_SIGNING_SECRET
    
    def create_lead_from_chat(self, organization, session_id, message, user_data=None):
        """Create lead from chat interaction"""
        # Extract contact info from message
        email = self.extract_email(message)
        phone = self.extract_phone(message)
        name = self.extract_name(message, user_data)
        
        # Create lead
        lead = Lead.objects.create(
            organization=organization,
            name=name,
            email=email,
            phone=phone,
            source='chat',
            conversation_id=session_id,
            attributes={
                'initial_message': message,
                'user_data': user_data or {},
                'captured_at': timezone.now().isoformat()
            }
        )
        
        # Log event
        Event.objects.create(
            organization=organization,
            kind='lead.created',
            meta={
                'lead_id': str(lead.id),
                'source': 'chat',
                'has_contact_info': bool(email or phone)
            }
        )
        
        # Queue webhooks
        self.queue_lead_webhooks(lead)
        
        return lead
    
    def create_lead_from_form(self, organization, form_data):
        """Create lead from form submission"""
        lead = Lead.objects.create(
            organization=organization,
            name=form_data.get('name', ''),
            email=form_data.get('email', ''),
            phone=form_data.get('phone', ''),
            buy_or_rent=form_data.get('buy_or_rent', 'buy'),
            budget_max=form_data.get('budget_max'),
            beds=form_data.get('beds'),
            areas=form_data.get('areas', ''),
            source='form',
            utm_source=form_data.get('utm_source', ''),
            utm_campaign=form_data.get('utm_campaign', ''),
            referrer=form_data.get('referrer', ''),
            consent_contact=form_data.get('consent_contact', False),
            attributes=form_data.get('attributes', {})
        )
        
        # Log event
        Event.objects.create(
            organization=organization,
            kind='lead.created',
            meta={
                'lead_id': str(lead.id),
                'source': 'form',
                'has_contact_info': bool(lead.email or lead.phone)
            }
        )
        
        # Queue webhooks
        self.queue_lead_webhooks(lead)
        
        return lead
    
    def extract_email(self, text):
        """Extract email from text"""
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group() if match else ''
    
    def extract_phone(self, text):
        """Extract phone number from text"""
        import re
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        match = re.search(phone_pattern, text)
        return match.group() if match else ''
    
    def extract_name(self, text, user_data=None):
        """Extract name from text or user data"""
        if user_data and user_data.get('name'):
            return user_data['name']
        
        # Simple name extraction (first two words)
        words = text.split()
        if len(words) >= 2:
            return f"{words[0]} {words[1]}"
        
        return 'Chat User'
    
    def queue_lead_webhooks(self, lead):
        """Queue webhook notifications for lead creation"""
        webhook_targets = ['n8n', 'hubspot', 'katalyst']
        
        for target in webhook_targets:
            payload = self.build_lead_webhook_payload(lead, target)
            
            WebhookOutbox.objects.create(
                organization=lead.organization,
                target=target,
                event_kind='lead.created',
                payload=payload
            )
    
    def build_lead_webhook_payload(self, lead, target):
        """Build webhook payload for different targets"""
        base_payload = {
            'event': 'lead.created',
            'organization_slug': lead.organization.slug,
            'lead': {
                'id': str(lead.id),
                'name': lead.name,
                'email': lead.email,
                'phone': lead.phone,
                'source': lead.source,
                'status': lead.status,
                'created_at': lead.created_at.isoformat(),
                'attributes': lead.attributes
            },
            'occurred_at': timezone.now().isoformat()
        }
        
        # Customize payload for different targets
        if target == 'hubspot':
            base_payload['lead']['properties'] = {
                'firstname': lead.name.split()[0] if lead.name else '',
                'lastname': ' '.join(lead.name.split()[1:]) if len(lead.name.split()) > 1 else '',
                'email': lead.email,
                'phone': lead.phone,
                'hs_lead_status': 'NEW',
                'lead_source': lead.source
            }
        
        elif target == 'n8n':
            base_payload['workflow'] = 'lead-processing'
            base_payload['lead']['conversation_id'] = lead.conversation_id
        
        return base_payload
    
    def sign_webhook_payload(self, payload):
        """Sign webhook payload with HMAC"""
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.webhook_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def send_webhook(self, webhook_outbox):
        """Send webhook with retry logic"""
        try:
            # Get webhook URL based on target
            webhook_url = self.get_webhook_url(webhook_outbox.target)
            
            # Sign payload
            signature = self.sign_webhook_payload(webhook_outbox.payload)
            
            # Send request
            headers = {
                'Content-Type': 'application/json',
                'X-KaTek-Signature': signature,
                'User-Agent': 'KaTek-Webhook/1.0'
            }
            
            response = requests.post(
                webhook_url,
                json=webhook_outbox.payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                webhook_outbox.status = 'sent'
                webhook_outbox.last_error = ''
            else:
                webhook_outbox.status = 'failed'
                webhook_outbox.last_error = f"HTTP {response.status_code}: {response.text[:500]}"
            
        except requests.exceptions.RequestException as e:
            webhook_outbox.status = 'failed'
            webhook_outbox.last_error = str(e)[:500]
        
        except Exception as e:
            webhook_outbox.status = 'failed'
            webhook_outbox.last_error = str(e)[:500]
        
        finally:
            webhook_outbox.attempts += 1
            webhook_outbox.save()
    
    def get_webhook_url(self, target):
        """Get webhook URL for target"""
        urls = {
            'n8n': getattr(settings, 'N8N_WEBHOOK_URL', 'https://your-n8n-instance.com/webhook/katek/ingest'),
            'hubspot': getattr(settings, 'HUBSPOT_WEBHOOK_URL', 'https://api.hubapi.com/contacts/v1/contact/'),
            'katalyst': getattr(settings, 'KATALYST_WEBHOOK_URL', 'https://your-katalyst-instance.com/api/leads')
        }
        return urls.get(target, '')
    
    def process_webhook_outbox(self):
        """Process pending webhooks with retry logic"""
        pending_webhooks = WebhookOutbox.objects.filter(
            status='pending',
            attempts__lt=3
        )[:10]  # Process in batches
        
        for webhook in pending_webhooks:
            self.send_webhook(webhook)
    
    def retry_failed_webhooks(self):
        """Retry failed webhooks with exponential backoff"""
        failed_webhooks = WebhookOutbox.objects.filter(
            status='failed',
            attempts__lt=3
        )[:10]
        
        for webhook in failed_webhooks:
            # Exponential backoff: 2^attempts minutes
            backoff_minutes = 2 ** webhook.attempts
            retry_time = timezone.now() + timezone.timedelta(minutes=backoff_minutes)
            
            if timezone.now() >= retry_time:
                webhook.status = 'pending'
                webhook.save()
                self.send_webhook(webhook)


class LeadQualificationService:
    """Service for lead qualification and scoring"""
    
    def qualify_lead(self, lead):
        """Qualify a lead based on available information"""
        score = 0
        criteria = {}
        
        # Contact information
        if lead.email:
            score += 30
            criteria['has_email'] = True
        if lead.phone:
            score += 30
            criteria['has_phone'] = True
        
        # Budget information
        if lead.budget_max:
            score += 20
            criteria['has_budget'] = True
        
        # Property preferences
        if lead.beds:
            score += 10
            criteria['has_bed_preference'] = True
        if lead.areas:
            score += 10
            criteria['has_area_preference'] = True
        
        # Engagement
        if lead.conversation_id:
            score += 10
            criteria['has_conversation'] = True
        
        # Determine qualification status
        if score >= 70:
            status = 'qualified'
        elif score >= 40:
            status = 'contacted'
        else:
            status = 'new'
        
        # Update lead
        lead.status = status
        lead.attributes.update({
            'qualification_score': score,
            'qualification_criteria': criteria,
            'qualified_at': timezone.now().isoformat() if status == 'qualified' else None
        })
        lead.save()
        
        # Log qualification event
        if status == 'qualified':
            Event.objects.create(
                organization=lead.organization,
                kind='lead.qualified',
                meta={
                    'lead_id': str(lead.id),
                    'score': score,
                    'criteria': criteria
                }
            )
        
        return {
            'status': status,
            'score': score,
            'criteria': criteria
        }
    
    def link_property_for_message(self, message):
        """Link property to message/lead using resolution pipeline"""
        if not message.lead:
            return None
        
        organization = message.organization
        text = message.text.lower()
        payload = message.raw_payload or {}
        
        # Resolution order (stop at first confident match)
        
        # 1. Explicit payload keys (property_id/slug/URL) → confidence=1.0
        property_id = payload.get('property_id')
        property_slug = payload.get('property_slug')
        property_url = payload.get('property_url')
        
        if property_id:
            try:
                prop = Property.objects.get(id=property_id, organization=organization)
                return self._create_link(message.lead, prop, 1.0, "Explicit property_id in payload")
            except Property.DoesNotExist:
                pass
        
        if property_slug:
            try:
                prop = Property.objects.get(slug=property_slug, organization=organization)
                return self._create_link(message.lead, prop, 1.0, "Explicit property_slug in payload")
            except Property.DoesNotExist:
                pass
        
        if property_url:
            # Extract slug from URL
            slug_match = re.search(r'/([^/]+)/?$', property_url)
            if slug_match:
                slug = slug_match.group(1)
                try:
                    prop = Property.objects.get(slug=slug, organization=organization)
                    return self._create_link(message.lead, prop, 1.0, "Explicit property_url in payload")
                except Property.DoesNotExist:
                    pass
        
        # 2. URL/slug regex from text → confidence ≥0.9
        url_pattern = r'(?:https?://)?(?:www\.)?[^/\s]+/([^/\s]+)/?'
        url_matches = re.findall(url_pattern, text)
        for slug in url_matches:
            try:
                prop = Property.objects.get(slug=slug, organization=organization)
                return self._create_link(message.lead, prop, 0.9, f"URL/slug regex match: {slug}")
            except Property.DoesNotExist:
                pass
        
        # Also check for property detail URLs
        property_url_pattern = r'/property/([^/\s]+)/?'
        property_matches = re.findall(property_url_pattern, text)
        for slug in property_matches:
            try:
                prop = Property.objects.get(slug=slug, organization=organization)
                return self._create_link(message.lead, prop, 0.9, f"Property URL match: {slug}")
            except Property.DoesNotExist:
                pass
        
        # 3. MLS/ref code lookup → confidence ≥0.85
        # Assuming MLS/ref codes might be in badges or description
        mls_pattern = r'\b(?:mls|ref)[\s:]*([a-z0-9-]+)\b'
        mls_matches = re.findall(mls_pattern, text, re.IGNORECASE)
        for code in mls_matches:
            props = Property.objects.filter(
                Q(badges__icontains=code) | Q(description__icontains=code),
                organization=organization,
                is_active=True
            )
            if props.exists():
                prop = props.first()
                return self._create_link(message.lead, prop, 0.85, f"MLS/ref code match: {code}")
        
        # 4. Fuzzy title/neighborhood + price proximity → confidence 0.6–0.8
        # Extract price mentions
        price_pattern = r'\$?([\d,]+)'
        price_matches = re.findall(price_pattern, text)
        mentioned_price = None
        if price_matches:
            try:
                # Take the largest price mentioned (likely the property price)
                prices = [int(p.replace(',', '')) for p in price_matches]
                mentioned_price = max(prices)
            except ValueError:
                pass
        
        # Extract neighborhood/city mentions
        city_pattern = r'\b(?:in|at|near|around|downtown|uptown)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
        city_matches = re.findall(city_pattern, text)
        
        # Extract property title keywords
        title_keywords = []
        for word in text.split():
            if len(word) > 3:  # Skip short words
                title_keywords.append(word)
        
        if title_keywords or city_matches or mentioned_price:
            query = Property.objects.filter(organization=organization)
            
            # Filter by city/area
            if city_matches:
                city_query = Q()
                for city in city_matches:
                    city_query |= Q(city__icontains=city) | Q(area__icontains=city)
                query = query.filter(city_query)
            
            # Filter by price proximity (±20%)
            if mentioned_price:
                price_min = int(mentioned_price * 0.8)
                price_max = int(mentioned_price * 1.2)
                query = query.filter(price_amount__gte=price_min, price_amount__lte=price_max)
            
            # Filter by title keywords
            if title_keywords:
                title_query = Q()
                for keyword in title_keywords[:5]:  # Limit to first 5 keywords
                    title_query |= Q(title__icontains=keyword)
                query = query.filter(title_query)
            
            matched_props = list(query[:5])  # Limit results
            
            if matched_props:
                # Calculate confidence based on match quality
                prop = matched_props[0]
                confidence = 0.6
                if mentioned_price:
                    price_diff = abs(prop.price_amount - mentioned_price) / mentioned_price
                    if price_diff < 0.1:  # Within 10%
                        confidence += 0.1
                if city_matches:
                    confidence += 0.1
                
                confidence = min(confidence, 0.8)  # Cap at 0.8
                
                return self._create_link(
                    message.lead,
                    prop,
                    confidence,
                    f"Fuzzy match: title/keywords/price proximity"
                )
        
        # 5. Vector search over property embeddings → confidence ≥0.78
        if organization:
            try:
                similar_props = vector_service.search_similar_properties(
                    organization,
                    message.text,
                    limit=3
                )
                
                if similar_props:
                    # Use first result if vector search returns meaningful results
                    # In production, you'd check similarity scores from pgvector
                    prop = similar_props[0]
                    return self._create_link(message.lead, prop, 0.78, "Vector similarity search")
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
        
        # No match found
        return None
    
    def _create_link(self, lead, property, confidence, evidence):
        """Create LeadPropertyLink with deduplication"""
        # Check if link already exists
        existing = LeadPropertyLink.objects.filter(
            lead=lead,
            property=property
        ).first()
        
        if existing:
            # Update if confidence is higher
            if confidence > existing.confidence:
                existing.confidence = confidence
                existing.evidence = evidence
                existing.save()
            return existing
        
        # Create new link
        return LeadPropertyLink.objects.create(
            organization=lead.organization,
            lead=lead,
            property=property,
            confidence=confidence,
            evidence=evidence
        )


# Global instances
lead_capture_service = LeadCaptureService()
lead_qualification_service = LeadQualificationService()
