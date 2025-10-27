from django.urls import path
from .views import (
    home, results, property_detail, property_chat, property_chat_simple, property_chat_ai,
    home_chat, property_modal,
    listing_choice, ai_prompt_listing, manual_form_listing,
    upload_listing, processing_listing, validation_chat, book, thanks, dashboard,
    lead_submit, health_check, readiness_check, ai_prompt_search, webhook_chat, init_webhook_chat,
    get_property_titles, landing, signup, login_view, logout_view, setup_wizard, properties, chat_agent, leads, campaigns, analytics, chat, settings, password_reset_request, password_reset_confirm,
    add_property_modal, sync_estimates_modal, bulk_actions_modal,
    use_cases, pricing, case_studies, resources, property_iq, lead_robot, ai_concierge, contact
)
from .views_oauth import custom_google_login, custom_google_callback, oauth_success, oauth_error, direct_google_oauth
from .views_google_oauth import google_oauth_login, google_oauth_callback, google_oauth_error
from .views_ai_validation import init_ai_validation_chat, ai_validation_chat
from .views_webhook import n8n_property_enrichment_callback, n8n_lead_processing_callback

urlpatterns = [
    path("", landing, name="home"),
    path("landing/", landing, name="landing"),
    path("signup/", signup, name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("setup/", setup_wizard, name="setup_wizard"),
    path("properties/", properties, name="properties"),
    path("chat-agent/", chat_agent, name="chat_agent"),
    path("leads/", leads, name="leads"),
    path("campaigns/", campaigns, name="campaigns"),
    path("analytics/", analytics, name="analytics"),
    path("chat/", chat, name="chat"),
    path("settings/", settings, name="settings"),
    path("password-reset/", password_reset_request, name="password_reset"),
    path("password-reset-confirm/<str:uidb64>/<str:token>/", password_reset_confirm, name="password_reset_confirm"),
    path("list", results, name="results"),
    path("property/<slug:slug>/", property_detail, name="property_detail"),
    path("property/<slug:slug>/chat", property_chat, name="property_chat"),
    path("property/<slug:slug>/chat-simple", property_chat_simple, name="property_chat_simple"),
    path("property/<slug:slug>/chat-ai", property_chat_ai, name="property_chat_ai"),
    path("property/<slug:slug>/modal", property_modal, name="property_modal"),
    path("home-chat", home_chat, name="home_chat"),

    path("listing-choice/", listing_choice, name="listing_choice"),
    path("ai-prompt-listing/", ai_prompt_listing, name="ai_prompt_listing"),
    path("manual-form-listing/", manual_form_listing, name="manual_form_listing"),

    path("upload-listing/", upload_listing, name="upload_listing"),
    path("processing/<uuid:upload_id>/", processing_listing, name="processing_listing"),
    path("validation/<uuid:upload_id>/", validation_chat, name="validation_chat"),

    path("lead/submit", lead_submit, name="lead_submit"),
    path("book", book, name="book"),
    path("thanks", thanks, name="thanks"),
    path("dashboard", dashboard, name="dashboard"),
    path("dashboard/", dashboard, name="dashboard_slash"),
    path("health/", health_check, name="health_check"),
    path("readiness/", readiness_check, name="readiness_check"),
    
    # NEW: AI Prompt Search with webhook response
    path("search/ai-prompt/", ai_prompt_search, name="ai_prompt_search"),
    
    # NEW: Webhook-powered AI chat
    path("chat/webhook/init/", init_webhook_chat, name="init_webhook_chat"),
    path("chat/webhook/", webhook_chat, name="webhook_chat"),
    
    # API: Property titles for auto-linking in chat
    path("api/properties/titles/", get_property_titles, name="get_property_titles"),
    
    # NEW: AI Validation Chat for property listings
    path("ai-validation/init/", init_ai_validation_chat, name="init_ai_validation_chat"),
    path("ai-validation/chat/", ai_validation_chat, name="ai_validation_chat"),
    
    # Modal endpoints for HTMX
    path("modal/add-property/", add_property_modal, name="add_property_modal"),
    path("modal/sync-estimates/<str:property_id>/", sync_estimates_modal, name="sync_estimates_modal"),
    path("modal/bulk-actions/", bulk_actions_modal, name="bulk_actions_modal"),
    
    # Webhook callbacks for n8n
    path("webhook/n8n/property-enrichment/", n8n_property_enrichment_callback, name="n8n_property_enrichment"),
    path("webhook/n8n/lead-processing/", n8n_lead_processing_callback, name="n8n_lead_processing"),
    
    # Public pages
    path("use-cases/", use_cases, name="use_cases"),
    path("pricing/", pricing, name="pricing"),
    path("case-studies/", case_studies, name="case_studies"),
    path("resources/", resources, name="resources"),
    
    # Product pages
    path("products/property-iq/", property_iq, name="property_iq"),
    path("products/lead-robot/", lead_robot, name="lead_robot"),
    path("products/ai-concierge/", ai_concierge, name="ai_concierge"),
    
    # Contact page
    path("contact/", contact, name="contact"),
    
    # Custom OAuth views
    path("oauth/google/login/", custom_google_login, name="custom_google_login"),
    path("oauth/google/callback/", custom_google_callback, name="custom_google_callback"),
    path("oauth/success/", oauth_success, name="oauth_success"),
    path("oauth/error/", oauth_error, name="oauth_error"),
    path("oauth/google/direct/", direct_google_oauth, name="direct_google_oauth"),
    
    # Our own Google OAuth (no allauth bullshit)
    path("google/login/", google_oauth_login, name="google_oauth_login"),
    path("google/callback/", google_oauth_callback, name="google_oauth_callback"),
    path("google/error/", google_oauth_error, name="google_oauth_error"),
]


