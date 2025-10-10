from django.urls import path
from .views import (
    home, results, property_detail, property_chat, property_chat_simple,
    home_chat, property_modal,
    listing_choice, ai_prompt_listing, manual_form_listing,
    upload_listing, processing_listing, validation_chat, book, thanks, dashboard,
    lead_submit, health_check, ai_prompt_search
)

urlpatterns = [
    path("", home, name="home"),
    path("list", results, name="results"),
    path("property/<slug:slug>/", property_detail, name="property_detail"),
    path("property/<slug:slug>/chat", property_chat, name="property_chat"),
    path("property/<slug:slug>/chat-simple", property_chat_simple, name="property_chat_simple"),
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
    path("health/", health_check, name="health_check"),
    
    # NEW: AI Prompt Search with webhook response
    path("search/ai-prompt/", ai_prompt_search, name="ai_prompt_search"),
]


