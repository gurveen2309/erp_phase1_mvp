from django.urls import path

from reporting import views


app_name = "reporting"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("ledger/", views.party_ledger_view, name="party-ledger"),
    path("ledger/pdf/", views.party_ledger_pdf_view, name="party-ledger-pdf"),
    path("challans/<int:challan_id>/receipt.pdf", views.challan_receipt_pdf_view, name="challan-receipt-pdf"),
    path("invoices/<int:invoice_id>/receipt.pdf", views.invoice_receipt_pdf_view, name="invoice-receipt-pdf"),
    path("outstanding/", views.outstanding_summary_view, name="outstanding-summary"),
    path("production/", views.production_dashboard_view, name="production-dashboard"),
]
