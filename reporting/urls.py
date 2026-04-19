from django.urls import path

from reporting import views


app_name = "reporting"

urlpatterns = [
    path("ledger/", views.party_ledger_view, name="party-ledger"),
    path("outstanding/", views.outstanding_summary_view, name="outstanding-summary"),
    path("production/", views.production_dashboard_view, name="production-dashboard"),
]
