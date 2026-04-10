from django.urls import path

from . import views

urlpatterns = [
    path("", views.root, name="root"),
    path("healthz", views.healthcheck, name="healthcheck"),
    path("api", views.api_meta, name="api-meta"),
    path("api/overview", views.overview, name="overview"),
    path("api/companies", views.list_companies, name="companies"),
    path("api/companies/<int:company_id>", views.company_detail, name="company-detail"),
    path("api/companies/<int:company_id>/dashboard", views.company_dashboard, name="company-dashboard"),
    path("api/companies/<int:company_id>/notes", views.company_notes, name="company-notes"),
    path("api/companies/<int:company_id>/sections", views.company_sections, name="company-sections"),
    path("api/companies/<int:company_id>/periods", views.company_periods, name="company-periods"),
    path("api/companies/<int:company_id>/financial", views.company_financial, name="company-financial"),
    path("api/companies/<int:company_id>/financial-table", views.company_financial_table, name="company-financial-table"),
    path("api/companies/<int:company_id>/key-metrics", views.company_key_metrics, name="company-key-metrics"),
    path("api/companies/<int:company_id>/health", views.company_health, name="company-health"),
    path("api/companies/<int:company_id>/health/export", views.export_health, name="company-health-export"),
    path("api/chat", views.chat, name="chat"),
]
