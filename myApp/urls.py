from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("list", views.results, name="results"),
    path("property/<slug:slug>/", views.property_detail, name="property_detail"),
    path("property/<slug:slug>/chat", views.property_chat, name="property_chat"),
    path("lead/submit", views.lead_submit, name="lead_submit"),
    path("book", views.book, name="book"),
    path("thanks", views.thanks, name="thanks"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("health/", views.health_check, name="health_check"),
]


