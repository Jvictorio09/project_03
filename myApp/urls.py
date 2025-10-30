from django.urls import path
from .views import (
    home, results, property_detail, property_chat, property_chat_simple, property_chat_ai,
    home_chat, property_modal,
    listing_choice, ai_prompt_listing, manual_form_listing,
    upload_listing, processing_listing, validation_chat, book, thanks, dashboard,
    lead_submit, health_check, readiness_check, ai_prompt_search, webhook_chat, init_webhook_chat,
    get_property_titles, landing, signup, login_view, logout_view, setup_wizard, properties, chat_agent, leads, campaigns, analytics, chat, settings, password_reset_request, password_reset_confirm,
    sync_estimates_modal, bulk_actions_modal,
    hide_property, unhide_property,
    use_cases, pricing, case_studies, resources, property_iq, lead_robot, ai_concierge, contact
)
from .views_properties_bulk import bulk_properties_action, export_properties
from .views_properties_import import (
    add_property_modal, edit_property_modal, import_manual, import_ai, import_csv,
    import_status, import_validate, import_validate_submit,
    import_complete, import_success, import_csv_template
)
from .views_properties_import_simple import import_csv_simple
from .views_oauth import custom_google_login, custom_google_callback, oauth_success, oauth_error, direct_google_oauth
from .views_google_oauth import google_oauth_login, google_oauth_callback, google_oauth_error
from .views_email_oauth import connect_gmail, email_oauth_callback, disconnect_gmail, set_primary_email
from .views_campaigns import create_campaign, edit_campaign, delete_campaign, add_campaign_step, send_campaign, campaign_stats
from .views_ai_validation import init_ai_validation_chat, ai_validation_chat
from .views_webhook import n8n_property_enrichment_callback, n8n_lead_processing_callback, property_enrichment_webhook, postmark_inbound, n8n_send_now, n8n_fail, n8n_due_messages, n8n_status, n8n_test
from .views_admin import ingestion_health
from .views_jobs import jobs_next, job_update
from .views_onboarding import onboarding_wizard, onboarding_step1_brand, onboarding_step2_persona, onboarding_step3_channels, onboarding_step4_plan, onboarding_step5_import, organization_settings, switch_organization
from .views_chat import public_chat, chat_api_ask, embed_widget_js
from .views_social import facebook_webhook, instagram_webhook, connect_facebook_page, connect_instagram_account

urlpatterns = [
    path("", landing, name="home"),
    path("landing/", landing, name="landing"),
    path("signup/", signup, name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("setup/", setup_wizard, name="setup_wizard"),
    path("onboarding/", onboarding_wizard, name="onboarding_wizard"),
    path("onboarding/step1/", onboarding_step1_brand, name="onboarding_step1"),
    path("onboarding/step2/", onboarding_step2_persona, name="onboarding_step2"),
    path("onboarding/step3/", onboarding_step3_channels, name="onboarding_step3"),
    path("onboarding/step4/", onboarding_step4_plan, name="onboarding_step4"),
    path("onboarding/step5/", onboarding_step5_import, name="onboarding_step5"),
    path("org/settings/", organization_settings, name="organization_settings"),
    path("org/switch/", switch_organization, name="switch_organization"),
    path("properties/", properties, name="properties"),
    path("api/properties/<uuid:property_id>/hide/", hide_property, name="hide_property"),
    path("api/properties/<uuid:property_id>/unhide/", unhide_property, name="unhide_property"),
    path("api/properties/bulk-action/", bulk_properties_action, name="bulk_properties_action"),
    path("api/properties/export/", export_properties, name="export_properties"),
    path("chat-agent/", chat_agent, name="chat_agent"),
    path("leads/", leads, name="leads"),
    path("campaigns/", campaigns, name="campaigns"),
    path("analytics/", analytics, name="analytics"),
    path("chat/", chat, name="chat"),
    path("settings/", settings, name="settings"),
    path("password-reset/", password_reset_request, name="password_reset"),
    path("password-reset-confirm/<str:uidb64>/<str:token>/", password_reset_confirm, name="password_reset_confirm"),
    
    # Public ChatURL routes
    path("chat/<str:org_slug>/", public_chat, name="public_chat"),
    path("api/chat/ask/", chat_api_ask, name="chat_api_ask"),
    path("embed/<str:org_slug>.js", embed_widget_js, name="embed_widget_js"),
    
    # Social Media Integration
    path("webhook/facebook/", facebook_webhook, name="facebook_webhook"),
    path("webhook/instagram/", instagram_webhook, name="instagram_webhook"),
    path("api/connect/facebook/", connect_facebook_page, name="connect_facebook"),
    path("api/connect/instagram/", connect_instagram_account, name="connect_instagram"),
    
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
    # Admin health page
    path("admin/ingestion/health/", ingestion_health, name="ingestion_health"),
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
    # Property Import (HTMX endpoints)
    path("modal/add-property/", add_property_modal, name="add_property_modal"),
    path("modal/edit-property/<uuid:property_id>/", edit_property_modal, name="edit_property_modal"),
    path("import/manual/", import_manual, name="import_manual"),
    path("import/ai/", import_ai, name="import_ai"),
    path("import/csv/", import_csv, name="import_csv"),  # Complex version (keeping for backward compat)
    path("import/csv-simple/", import_csv_simple, name="import_csv_simple"),  # Simple version - USE THIS
    path("import/csv/template/", import_csv_template, name="import_csv_template"),
    path("import/status/<uuid:upload_id>/", import_status, name="import_status"),
    path("import/validate/<uuid:upload_id>/", import_validate, name="import_validate"),
    path("import/validate/<uuid:upload_id>/submit/", import_validate_submit, name="import_validate_submit"),
    path("import/complete/<uuid:upload_id>/", import_complete, name="import_complete"),
    path("import/success/<uuid:property_id>/", import_success, name="import_success"),
    path("modal/sync-estimates/<str:property_id>/", sync_estimates_modal, name="sync_estimates_modal"),
    path("modal/bulk-actions/", bulk_actions_modal, name="bulk_actions_modal"),
    
    # Webhook callbacks for n8n
    path("webhook/n8n/property-enrichment/", n8n_property_enrichment_callback, name="n8n_property_enrichment"),
    path("webhook/n8n/lead-processing/", n8n_lead_processing_callback, name="n8n_lead_processing"),
    path("webhook/n8n/send-now/", n8n_send_now, name="n8n_send_now"),
    path("webhook/n8n/fail/", n8n_fail, name="n8n_fail"),
    path("webhook/n8n/due-messages/", n8n_due_messages, name="n8n_due_messages"),
    
    # n8n integration testing
    path("api/n8n/status/", n8n_status, name="n8n_status"),
    path("api/n8n/test/", n8n_test, name="n8n_test"),
    path("webhook-test/enrich-property/", property_enrichment_webhook, name="property_enrichment_webhook"),
    
    # Inbound email webhook
    path("webhook/postmark/inbound/", postmark_inbound, name="postmark_inbound"),
    
    # Jobs API for n8n
    path("api/jobs/next/", jobs_next, name="jobs_next"),
    path("api/jobs/<uuid:job_id>/", job_update, name="job_update"),
    path("api/jobs/<uuid:job_id>/callback/", job_update, name="job_callback"),
    
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
    
    # Email OAuth for campaigns
    path("email/connect/", connect_gmail, name="connect_gmail"),
    path("email/oauth/callback/", email_oauth_callback, name="email_oauth_callback"),
    path("email/disconnect/<uuid:email_account_id>/", disconnect_gmail, name="disconnect_gmail"),
    path("email/set-primary/<uuid:email_account_id>/", set_primary_email, name="set_primary_email"),
    
    # Campaign management
    path("campaigns/create/", create_campaign, name="create_campaign"),
    path("campaigns/edit/<uuid:campaign_id>/", edit_campaign, name="edit_campaign"),
    path("campaigns/delete/<uuid:campaign_id>/", delete_campaign, name="delete_campaign"),
    path("campaigns/<uuid:campaign_id>/add-step/", add_campaign_step, name="add_campaign_step"),
    path("campaigns/<uuid:campaign_id>/send/", send_campaign, name="send_campaign"),
    path("campaigns/<uuid:campaign_id>/stats/", campaign_stats, name="campaign_stats"),
]


