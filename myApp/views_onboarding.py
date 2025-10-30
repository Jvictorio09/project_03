"""
Onboarding wizard views for new organizations
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings
import stripe
import json

from .models import Organization, Membership, Plan, Subscription
from .services_organization import OrganizationService
from .decorators_organization import org_member_required


@login_required
def onboarding_wizard(request):
    """Multi-step onboarding wizard"""
    # Check if user already has an organization
    user_orgs = OrganizationService.get_user_organizations(request.user)
    if user_orgs.exists():
        return redirect('/dashboard')
    
    step = request.GET.get('step', '1')
    
    if step == '1':
        return render(request, 'onboarding/step1_brand.html')
    elif step == '2':
        return render(request, 'onboarding/step2_persona.html')
    elif step == '3':
        return render(request, 'onboarding/step3_channels.html')
    elif step == '4':
        return render(request, 'onboarding/step4_plan.html')
    elif step == '5':
        return render(request, 'onboarding/step5_import.html')
    else:
        return render(request, 'onboarding/step1_brand.html')


@login_required
@require_POST
def onboarding_step1_brand(request):
    """Step 1: Brand setup"""
    name = request.POST.get('name', '').strip()
    logo_url = request.POST.get('logo_url', '').strip()
    brand_primary = request.POST.get('brand_primary', '#6D28D9')
    brand_accent = request.POST.get('brand_accent', '#18AFAB')
    
    if not name:
        messages.error(request, 'Organization name is required.')
        return redirect('/onboarding/?step=1')
    
    # Store in session for later use
    request.session['onboarding_data'] = {
        'name': name,
        'logo_url': logo_url,
        'brand_primary': brand_primary,
        'brand_accent': brand_accent
    }
    
    return redirect('/onboarding/?step=2')


@login_required
@require_POST
def onboarding_step2_persona(request):
    """Step 2: Agent persona setup"""
    agent_persona = request.POST.get('agent_persona', 'friendly_consultant')
    tone_formality = int(request.POST.get('tone_formality', 70))
    tone_warmth = int(request.POST.get('tone_warmth', 80))
    tone_assertiveness = int(request.POST.get('tone_assertiveness', 60))
    chat_greeting = request.POST.get('chat_greeting', '').strip()
    
    # Update session data
    if 'onboarding_data' not in request.session:
        request.session['onboarding_data'] = {}
    
    request.session['onboarding_data'].update({
        'agent_persona': agent_persona,
        'tone_formality': tone_formality,
        'tone_warmth': tone_warmth,
        'tone_assertiveness': tone_assertiveness,
        'chat_greeting': chat_greeting
    })
    
    return redirect('/onboarding/?step=3')


@login_required
@require_POST
def onboarding_step3_channels(request):
    """Step 3: Channel connections (placeholder)"""
    # For now, just store that channels step is complete
    if 'onboarding_data' not in request.session:
        request.session['onboarding_data'] = {}
    
    request.session['onboarding_data']['channels_complete'] = True
    
    return redirect('/onboarding/?step=4')


@login_required
@require_POST
def onboarding_step4_plan(request):
    """Step 4: Plan selection"""
    plan_code = request.POST.get('plan', 'starter')
    
    try:
        # Ensure plans exist, create if not
        if not Plan.objects.exists():
            OrganizationService.create_default_plans()
        
        plan = Plan.objects.get(code=plan_code)
        
        # Update session data
        if 'onboarding_data' not in request.session:
            request.session['onboarding_data'] = {}
        
        request.session['onboarding_data']['plan_code'] = plan_code
        
        # Create organization with all collected data
        org_data = request.session.get('onboarding_data', {})
        
        # Generate unique slug
        org_name = org_data.get('name', f"{request.user.email.split('@')[0].title()} Real Estate")
        if not org_name or org_name.strip() == '':
            org_name = f"{request.user.email.split('@')[0].title()} Real Estate"
        
        base_slug = slugify(org_name)
        slug = base_slug
        counter = 1
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        organization = Organization.objects.create(
            name=org_name,
            slug=slug,
            logo_url=org_data.get('logo_url', ''),
            brand_primary=org_data.get('brand_primary', '#6D28D9'),
            brand_accent=org_data.get('brand_accent', '#18AFAB'),
            agent_persona=org_data.get('agent_persona', 'friendly_consultant'),
            tone_formality=org_data.get('tone_formality', 70),
            tone_warmth=org_data.get('tone_warmth', 80),
            tone_assertiveness=org_data.get('tone_assertiveness', 60),
            chat_greeting=org_data.get('chat_greeting', "Hello! I'm here to help you find your perfect property. What are you looking for today?"),
            created_by=request.user
        )
        
        # Create owner membership
        Membership.objects.create(
            user=request.user,
            organization=organization,
            role='owner',
            is_active=True
        )
        
        # Create subscription
        Subscription.objects.create(
            organization=organization,
            plan=plan,
            status='trialing',
            current_period_end=timezone.now() + timezone.timedelta(days=14)
        )
        
        # Set as active organization
        request.session['active_organization_id'] = str(organization.id)
        
        # Clear onboarding data
        if 'onboarding_data' in request.session:
            del request.session['onboarding_data']
        
        messages.success(request, f'Welcome to {organization.name}! Your organization has been created.')
        
        # Redirect to Stripe checkout for paid plans
        if plan_code != 'starter':
            return redirect(f'/billing/checkout?plan={plan_code}')
        
        return redirect('/onboarding/?step=5')
        
    except Plan.DoesNotExist:
        messages.error(request, 'Invalid plan selected. Please try again.')
        return redirect('/onboarding/?step=4')
    except Exception as e:
        import traceback
        messages.error(request, f'An error occurred: {str(e)}')
        print(f"Error creating organization: {traceback.format_exc()}")
        return redirect('/onboarding/?step=4')


@login_required
def onboarding_step5_import(request):
    """Step 5: Import listings"""
    # Check if user has an organization, if not redirect back
    if not hasattr(request, 'organization') or not request.organization:
        # Try to get organization from session
        active_org_id = request.session.get('active_organization_id')
        if active_org_id:
            try:
                from .models import Organization
                org = Organization.objects.get(id=active_org_id)
                # Verify membership
                from .models import Membership
                if Membership.objects.filter(user=request.user, organization=org, is_active=True).exists():
                    request.organization = org
                else:
                    messages.error(request, 'Please complete the onboarding process.')
                    return redirect('/onboarding/?step=1')
            except:
                messages.error(request, 'Please complete the onboarding process.')
                return redirect('/onboarding/?step=1')
        else:
            messages.error(request, 'Please complete the onboarding process.')
            return redirect('/onboarding/?step=1')
    
    if request.method == 'POST':
        import_type = request.POST.get('import_type', 'manual')
        
        if import_type == 'csv':
            # Handle CSV upload
            messages.info(request, 'CSV upload feature coming soon!')
        elif import_type == 'ai_prompt':
            # Handle AI prompt
            messages.info(request, 'AI prompt import feature coming soon!')
        elif import_type == 'manual':
            # Skip to dashboard
            messages.success(request, 'You can add listings manually from the dashboard.')
            return redirect('/dashboard')
        
        return redirect('/onboarding/?step=5')
    
    return render(request, 'onboarding/step5_import.html')


@login_required
@org_member_required(['owner', 'admin'])
def organization_settings(request):
    """Organization settings page"""
    if request.method == 'POST':
        # Update organization settings
        organization = request.organization
        
        organization.name = request.POST.get('name', organization.name)
        organization.logo_url = request.POST.get('logo_url', organization.logo_url)
        organization.brand_primary = request.POST.get('brand_primary', organization.brand_primary)
        organization.brand_accent = request.POST.get('brand_accent', organization.brand_accent)
        organization.agent_persona = request.POST.get('agent_persona', organization.agent_persona)
        organization.tone_formality = int(request.POST.get('tone_formality', organization.tone_formality))
        organization.tone_warmth = int(request.POST.get('tone_warmth', organization.tone_warmth))
        organization.tone_assertiveness = int(request.POST.get('tone_assertiveness', organization.tone_assertiveness))
        organization.chat_greeting = request.POST.get('chat_greeting', organization.chat_greeting)
        organization.timezone = request.POST.get('timezone', organization.timezone)
        
        organization.save()
        
        messages.success(request, 'Organization settings updated successfully.')
        return redirect('/settings')
    
    return render(request, 'settings/organization.html')


@login_required
@org_member_required(['owner', 'admin'])
def switch_organization(request):
    """Switch active organization"""
    if request.method == 'POST':
        organization_id = request.POST.get('organization_id')
        
        if OrganizationService.switch_organization(request, organization_id):
            messages.success(request, 'Organization switched successfully.')
        else:
            messages.error(request, 'Unable to switch organization.')
    
    return redirect(request.META.get('HTTP_REFERER', '/dashboard'))
