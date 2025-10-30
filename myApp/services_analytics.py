"""
Analytics service for dashboard metrics
"""
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import Event, Lead, Property, Organization, MessageLog, Campaign
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for generating analytics and metrics"""
    
    def get_dashboard_metrics(self, organization, days=30):
        """Get key dashboard metrics for organization"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        metrics = {}
        
        # Lead metrics
        metrics['leads'] = self.get_lead_metrics(organization, start_date, end_date)
        
        # Property metrics
        metrics['properties'] = self.get_property_metrics(organization)
        
        # Chat metrics
        metrics['chat'] = self.get_chat_metrics(organization, start_date, end_date)
        
        # Campaign metrics
        metrics['campaigns'] = self.get_campaign_metrics(organization, start_date, end_date)
        
        # Conversion metrics
        metrics['conversions'] = self.get_conversion_metrics(organization, start_date, end_date)
        
        return metrics
    
    def get_lead_metrics(self, organization, start_date, end_date):
        """Get lead-related metrics"""
        leads = Lead.objects.filter(
            organization=organization,
            created_at__range=[start_date, end_date]
        )
        
        total_leads = leads.count()
        # The Lead model does not currently support pipeline statuses.
        # Keep placeholders at 0 until a status field is introduced.
        qualified_leads = 0
        converted_leads = 0
        
        # Lead sources
        # Use UTM source captured from forms/landing pages
        sources = leads.values('utm_source').annotate(count=Count('id')).order_by('-count')
        
        # Daily lead trend
        daily_leads = leads.extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        return {
            'total': total_leads,
            'qualified': qualified_leads,
            'converted': converted_leads,
            'qualification_rate': (qualified_leads / total_leads * 100) if total_leads > 0 else 0,
            'conversion_rate': (converted_leads / total_leads * 100) if total_leads > 0 else 0,
            'sources': list(sources),
            'daily_trend': list(daily_leads)
        }
    
    def get_property_metrics(self, organization):
        """Get property-related metrics"""
        properties = Property.objects.filter(organization=organization)
        
        total_properties = properties.count()
        active_properties = properties.filter(is_active=True).count()
        
        # Average price
        avg_price = properties.aggregate(avg_price=Avg('price_amount'))['avg_price'] or 0
        
        # Price range
        price_stats = properties.aggregate(
            min_price=Avg('price_amount'),
            max_price=Avg('price_amount')
        )
        
        # Properties by city
        city_stats = properties.values('city').annotate(count=Count('id')).order_by('-count')[:5]
        
        return {
            'total': total_properties,
            'active': active_properties,
            'avg_price': avg_price,
            'city_breakdown': list(city_stats)
        }
    
    def get_chat_metrics(self, organization, start_date, end_date):
        """Get chat-related metrics"""
        chat_events = Event.objects.filter(
            organization=organization,
            kind__in=['chat.message_user', 'chat.message_agent'],
            created_at__range=[start_date, end_date]
        )
        
        user_messages = chat_events.filter(kind='chat.message_user').count()
        agent_messages = chat_events.filter(kind='chat.message_agent').count()
        
        # Daily chat activity
        daily_chats = chat_events.extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        return {
            'user_messages': user_messages,
            'agent_messages': agent_messages,
            'total_conversations': user_messages,  # Assuming 1 conversation per user message
            'daily_activity': list(daily_chats)
        }
    
    def get_campaign_metrics(self, organization, start_date, end_date):
        """Get campaign-related metrics"""
        campaigns = Campaign.objects.filter(organization=organization)
        
        total_campaigns = campaigns.count()
        active_campaigns = campaigns.filter(status='active').count()
        
        # Message logs for the period
        message_logs = MessageLog.objects.filter(
            organization=organization,
            created_at__range=[start_date, end_date]
        )
        
        total_sent = message_logs.count()
        total_delivered = message_logs.filter(status='delivered').count()
        total_opened = message_logs.filter(status='opened').count()
        total_clicked = message_logs.filter(status='clicked').count()
        
        return {
            'total_campaigns': total_campaigns,
            'active_campaigns': active_campaigns,
            'total_sent': total_sent,
            'total_delivered': total_delivered,
            'total_opened': total_opened,
            'total_clicked': total_clicked,
            'delivery_rate': (total_delivered / total_sent * 100) if total_sent > 0 else 0,
            'open_rate': (total_opened / total_delivered * 100) if total_delivered > 0 else 0,
            'click_rate': (total_clicked / total_opened * 100) if total_opened > 0 else 0
        }
    
    def get_conversion_metrics(self, organization, start_date, end_date):
        """Get conversion and funnel metrics"""
        # Lead funnel
        total_leads = Lead.objects.filter(
            organization=organization,
            created_at__range=[start_date, end_date]
        ).count()
        
        contacted_leads = Lead.objects.filter(
            organization=organization,
            status__in=['contacted', 'qualified', 'converted'],
            created_at__range=[start_date, end_date]
        ).count()
        
        qualified_leads = Lead.objects.filter(
            organization=organization,
            status__in=['qualified', 'converted'],
            created_at__range=[start_date, end_date]
        ).count()
        
        converted_leads = Lead.objects.filter(
            organization=organization,
            status='converted',
            created_at__range=[start_date, end_date]
        ).count()
        
        return {
            'total_leads': total_leads,
            'contacted_leads': contacted_leads,
            'qualified_leads': qualified_leads,
            'converted_leads': converted_leads,
            'contact_rate': (contacted_leads / total_leads * 100) if total_leads > 0 else 0,
            'qualification_rate': (qualified_leads / contacted_leads * 100) if contacted_leads > 0 else 0,
            'conversion_rate': (converted_leads / qualified_leads * 100) if qualified_leads > 0 else 0
        }
    
    def get_chart_data(self, organization, chart_type, days=30):
        """Get data for specific chart types"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        if chart_type == 'leads_over_time':
            return self.get_leads_over_time_data(organization, start_date, end_date)
        elif chart_type == 'chat_activity':
            return self.get_chat_activity_data(organization, start_date, end_date)
        elif chart_type == 'lead_sources':
            return self.get_lead_sources_data(organization, start_date, end_date)
        elif chart_type == 'conversion_funnel':
            return self.get_conversion_funnel_data(organization, start_date, end_date)
        elif chart_type == 'campaign_performance':
            return self.get_campaign_performance_data(organization, start_date, end_date)
        
        return {}
    
    def get_leads_timeseries(self, organization, days=7, connected_channels=None):
        """Get leads timeseries data with zero-fill for missing days"""
        import pytz
        from datetime import timedelta
        
        if connected_channels is None:
            connected_channels = ['chat']  # Default
        
        tz = pytz.timezone('Asia/Manila')
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get actual lead counts per day
        leads = Lead.objects.filter(
            organization=organization,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).extra(
            select={'day': "date(created_at)"}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        # Convert to dict for lookup
        leads_dict = {str(item['day']): item['count'] for item in leads}
        
        # Generate all days in range with zero-fill
        series = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            date_str = str(current_date)
            count = leads_dict.get(date_str, 0)
            series.append({
                'date': date_str,
                'count': count
            })
            current_date += timedelta(days=1)
        
        return series
    
    def get_chat_activity_data(self, organization, start_date, end_date):
        """Get chat activity data for chart"""
        chat_events = Event.objects.filter(
            organization=organization,
            kind__in=['chat.message_user', 'chat.message_agent'],
            created_at__range=[start_date, end_date]
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        return {
            'labels': [str(item['day']) for item in chat_events],
            'datasets': [{
                'label': 'Chat Messages',
                'data': [item['count'] for item in chat_events],
                'borderColor': '#10b981',
                'backgroundColor': '#10b98120',
                'fill': True
            }]
        }
    
    def get_lead_sources_data(self, organization, start_date, end_date):
        """Get lead sources data for chart"""
        sources = Lead.objects.filter(
            organization=organization,
            created_at__range=[start_date, end_date]
        ).values('utm_source').annotate(count=Count('id')).order_by('-count')
        
        return {
            'labels': [item['utm_source'] or 'unknown' for item in sources],
            'datasets': [{
                'label': 'Leads',
                'data': [item['count'] for item in sources],
                'backgroundColor': [
                    '#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'
                ]
            }]
        }
    
    def get_conversion_funnel_data(self, organization, start_date, end_date):
        """Get conversion funnel data for chart"""
        total_leads = Lead.objects.filter(
            organization=organization,
            created_at__range=[start_date, end_date]
        ).count()
        
        # Pipeline metrics are not available without a status field on Lead
        contacted_leads = 0
        qualified_leads = 0
        converted_leads = 0
        
        return {
            'labels': ['Total Leads', 'Contacted', 'Qualified', 'Converted'],
            'datasets': [{
                'label': 'Leads',
                'data': [total_leads, contacted_leads, qualified_leads, converted_leads],
                'backgroundColor': ['#6366f1', '#10b981', '#f59e0b', '#ef4444']
            }]
        }
    
    def get_campaign_performance_data(self, organization, start_date, end_date):
        """Get campaign performance data for chart"""
        campaigns = Campaign.objects.filter(organization=organization)
        
        campaign_data = []
        for campaign in campaigns:
            message_logs = MessageLog.objects.filter(
                campaign=campaign,
                created_at__range=[start_date, end_date]
            )
            
            total_sent = message_logs.count()
            total_opened = message_logs.filter(status='opened').count()
            total_clicked = message_logs.filter(status='clicked').count()
            
            campaign_data.append({
                'name': campaign.name,
                'sent': total_sent,
                'opened': total_opened,
                'clicked': total_clicked,
                'open_rate': (total_opened / total_sent * 100) if total_sent > 0 else 0,
                'click_rate': (total_clicked / total_opened * 100) if total_opened > 0 else 0
            })
        
        return campaign_data


# Global instance
analytics_service = AnalyticsService()
