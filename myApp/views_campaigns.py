"""
Campaign management views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from django.db import transaction
import logging
import json
import hmac
import hashlib
import requests

from .models import Campaign, CampaignStep, Lead, EmailAccount, MessageLog, Company
from .forms import CampaignForm, CampaignStepForm
from .services_gmail import GmailService

logger = logging.getLogger(__name__)


def get_company(request):
    """Get company from request"""
    company = getattr(request, 'company', None)
    if not company:
        # Fallback: get from user's company
        company = Company.objects.filter(users=request.user).first()
    
    if not company:
        raise ValueError('No company found')
    
    return company


@login_required
@require_http_methods(["GET", "POST"])
def create_campaign(request):
    """Create a new campaign"""
    try:
        company = get_company(request)
        
        if request.method == 'POST':
            form = CampaignForm(request.POST)
            if form.is_valid():
                campaign = form.save(commit=False)
                campaign.company = company
                campaign.save()
                
                messages.success(request, f'Campaign "{campaign.name}" created successfully!')
                return redirect('campaigns')
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = CampaignForm()
        
        context = {
            'form': form,
            'campaign_types': Campaign.TYPE_CHOICES,
            'campaign_statuses': Campaign.STATUS_CHOICES
        }
        
        return render(request, 'campaigns/create_campaign.html', context)
        
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('campaigns')
    except Exception as e:
        logger.error(f"Error creating campaign: {e}", exc_info=True)
        messages.error(request, 'Failed to create campaign. Please try again.')
        return redirect('campaigns')


@login_required
@require_http_methods(["GET", "POST"])
def edit_campaign(request, campaign_id):
    """Edit an existing campaign"""
    try:
        company = get_company(request)
        campaign = get_object_or_404(Campaign, id=campaign_id, company=company)
        
        if request.method == 'POST':
            form = CampaignForm(request.POST, instance=campaign)
            if form.is_valid():
                form.save()
                messages.success(request, f'Campaign "{campaign.name}" updated successfully!')
                return redirect('campaigns')
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = CampaignForm(instance=campaign)
        
        # Get campaign steps
        campaign_steps = CampaignStep.objects.filter(campaign=campaign).order_by('order')
        
        context = {
            'form': form,
            'campaign': campaign,
            'campaign_steps': campaign_steps,
            'campaign_types': Campaign.TYPE_CHOICES,
            'campaign_statuses': Campaign.STATUS_CHOICES
        }
        
        return render(request, 'campaigns/edit_campaign.html', context)
        
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('campaigns')
    except Exception as e:
        logger.error(f"Error editing campaign: {e}", exc_info=True)
        messages.error(request, 'Failed to edit campaign. Please try again.')
        return redirect('campaigns')


@login_required
@require_POST
def delete_campaign(request, campaign_id):
    """Delete a campaign"""
    try:
        company = get_company(request)
        campaign = get_object_or_404(Campaign, id=campaign_id, company=company)
        
        campaign_name = campaign.name
        campaign.delete()
        
        messages.success(request, f'Campaign "{campaign_name}" deleted successfully!')
        return redirect('campaigns')
        
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('campaigns')
    except Exception as e:
        logger.error(f"Error deleting campaign: {e}", exc_info=True)
        messages.error(request, 'Failed to delete campaign. Please try again.')
        return redirect('campaigns')


@login_required
@require_http_methods(["GET", "POST"])
def add_campaign_step(request, campaign_id):
    """Add a step to a campaign"""
    try:
        company = get_company(request)
        campaign = get_object_or_404(Campaign, id=campaign_id, company=company)
        
        if request.method == 'POST':
            form = CampaignStepForm(request.POST)
            if form.is_valid():
                step = form.save(commit=False)
                step.campaign = campaign
                
                # Set order (next in sequence)
                last_step = CampaignStep.objects.filter(campaign=campaign).order_by('-order').first()
                step.order = (last_step.order + 1) if last_step else 1
                
                step.save()
                
                messages.success(request, f'Step "{step.name}" added to campaign!')
                return redirect('edit_campaign', campaign_id=campaign.id)
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = CampaignStepForm()
        
        context = {
            'form': form,
            'campaign': campaign
        }
        
        return render(request, 'campaigns/add_campaign_step.html', context)
        
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('campaigns')
    except Exception as e:
        logger.error(f"Error adding campaign step: {e}", exc_info=True)
        messages.error(request, 'Failed to add campaign step. Please try again.')
        return redirect('campaigns')


@login_required
@require_POST
def send_campaign(request, campaign_id):
    """Send a campaign to all leads"""
    try:
        # Get organization from request context
        organization = getattr(request, 'organization', None)
        if not organization:
            messages.error(request, 'No organization found. Please select an organization.')
            return redirect('campaigns')
        
        campaign = get_object_or_404(Campaign, id=campaign_id, organization=organization)
        
        # Check if campaign has steps
        campaign_steps = CampaignStep.objects.filter(campaign=campaign).order_by('order')
        if not campaign_steps.exists():
            messages.error(request, 'Campaign has no steps. Please add at least one step.')
            return redirect('edit_campaign', campaign_id=campaign.id)
        
        # Get primary email account
        email_account = EmailAccount.objects.filter(
            organization=organization,
            is_active=True,
            is_primary=True
        ).first()
        
        if not email_account:
            messages.error(request, 'No primary email account found. Please connect a Gmail account first.')
            return redirect('settings')
        
        # Get all leads for the organization
        leads = Lead.objects.filter(organization=organization, email__isnull=False).exclude(email='')
        if not leads.exists():
            messages.error(request, 'No leads found. Please add some leads first.')
            return redirect('leads')
        
        # Check n8n configuration
        use_n8n = getattr(settings, 'USE_N8N_ORCHESTRATION', False)
        n8n_webhook = getattr(settings, 'N8N_QUEUE_WEBHOOK_URL', '')
        n8n_secret = getattr(settings, 'N8N_HMAC_SECRET', '')
        
        logger.info(f"Campaign send: use_n8n={use_n8n}, n8n_webhook={'set' if n8n_webhook else 'not set'}")
        
        # Send or queue campaign
        gmail_service = GmailService()
        sent_count = 0
        error_count = 0
        
        first_step = campaign_steps.first()
        for lead in leads:
            try:
                if use_n8n and n8n_webhook and n8n_secret:
                    # Queue via n8n
                    payload = {
                        'message_log_id': '',
                        'campaign_id': str(campaign.id),
                        'step_id': str(first_step.id),
                        'lead_id': str(lead.id),
                        'organization_id': str(organization.id),
                        'send_at': timezone.now().isoformat(),
                        'request_id': f"{campaign.id}:{first_step.id}:{lead.id}",
                        'created_at': timezone.now().isoformat()
                    }
                    body = json.dumps(payload)
                    ts = str(int(timezone.now().timestamp()))
                    sig = hmac.new(n8n_secret.encode('utf-8'), f"{ts}.{body}".encode('utf-8'), hashlib.sha256).hexdigest()
                    headers = {
                        'Content-Type': 'application/json',
                        'X-Timestamp': ts,
                        'X-Signature': f"sha256={sig}"
                    }
                    logger.info(f"Queuing via n8n: {lead.email}")
                    resp = requests.post(n8n_webhook, data=body, headers=headers, timeout=15)
                    if resp.status_code in (200, 201, 202):
                        sent_count += 1
                        logger.info(f"Successfully queued: {lead.email}")
                    else:
                        error_count += 1
                        logger.error(f"n8n queue failed: {resp.status_code} - {resp.text}")
                else:
                    # Immediate send via Gmail
                    logger.info(f"Sending directly via Gmail: {lead.email}")
                    result = gmail_service.send_campaign_email(
                        email_account=email_account,
                        lead=lead,
                        campaign=campaign,
                        campaign_step=first_step
                    )
                    if result.get('success', False):
                        MessageLog.objects.create(
                            organization=organization,
                            campaign=campaign,
                            campaign_step=first_step,
                            lead=lead,
                            email_account=email_account,
                            status='sent',
                            message_id=result.get('message_id', ''),
                            provider=result.get('provider', 'gmail')
                        )
                        sent_count += 1
                    else:
                        MessageLog.objects.create(
                            organization=organization,
                            campaign=campaign,
                            campaign_step=first_step,
                            lead=lead,
                            email_account=email_account,
                            status='failed',
                            error_message=result.get('error', 'Unknown error')
                        )
                        error_count += 1
            except Exception as e:
                logger.error(f"Error sending/queuing campaign email to {lead.email}: {e}")
                error_count += 1
        
        # Update campaign status
        campaign.status = 'active'
        campaign.save()
        
        if sent_count > 0:
            messages.success(request, f'Campaign sent to {sent_count} leads successfully!')
        if error_count > 0:
            messages.warning(request, f'{error_count} emails failed to send.')
        
        return redirect('campaigns')
        
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('campaigns')
    except Exception as e:
        logger.error(f"Error sending campaign: {e}", exc_info=True)
        messages.error(request, 'Failed to send campaign. Please try again.')
        return redirect('campaigns')


@login_required
def campaign_stats(request, campaign_id):
    """Get campaign statistics"""
    try:
        company = get_company(request)
        campaign = get_object_or_404(Campaign, id=campaign_id, company=company)
        
        # Get message logs for this campaign
        message_logs = MessageLog.objects.filter(campaign=campaign)
        
        # Calculate stats
        total_sent = message_logs.filter(status='sent').count()
        total_delivered = message_logs.filter(status='delivered').count()
        total_opened = message_logs.filter(status='opened').count()
        total_clicked = message_logs.filter(status='clicked').count()
        total_failed = message_logs.filter(status='failed').count()
        
        # Calculate rates
        open_rate = (total_opened / total_delivered * 100) if total_delivered > 0 else 0
        click_rate = (total_clicked / total_delivered * 100) if total_delivered > 0 else 0
        
        stats = {
            'total_sent': total_sent,
            'total_delivered': total_delivered,
            'total_opened': total_opened,
            'total_clicked': total_clicked,
            'total_failed': total_failed,
            'open_rate': round(open_rate, 1),
            'click_rate': round(click_rate, 1)
        }
        
        return JsonResponse(stats)
        
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error getting campaign stats: {e}", exc_info=True)
        return JsonResponse({'error': 'Failed to get campaign statistics'}, status=500)
