from django.urls import path

from reporting import views


app_name = "reporting"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("templates/", views.blank_templates_view, name="blank-templates"),
    path("templates/process/", views.process_report_form_view, name="process-report-form"),
    path("history/", views.report_history_view, name="report-history"),
    path("templates/process.pdf", views.blank_process_template_pdf_view, name="blank-process-template-pdf"),
    path("templates/inspection.pdf", views.blank_inspection_template_pdf_view, name="blank-inspection-template-pdf"),
    path("ledger/", views.party_ledger_view, name="party-ledger"),
    path("ledger/pdf/", views.party_ledger_pdf_view, name="party-ledger-pdf"),
    path("challans/<int:challan_id>/receipt.pdf", views.challan_receipt_pdf_view, name="challan-receipt-pdf"),
    path("invoices/<int:invoice_id>/receipt.pdf", views.invoice_receipt_pdf_view, name="invoice-receipt-pdf"),
    path("invoices/<int:invoice_id>/process-uploaded.pdf", views.invoice_process_uploaded_pdf_view, name="invoice-process-uploaded-pdf"),
    path("invoices/<int:invoice_id>/inspection-uploaded.pdf", views.invoice_inspection_uploaded_pdf_view, name="invoice-inspection-uploaded-pdf"),
    path("outstanding/", views.outstanding_summary_view, name="outstanding-summary"),
    path("production/", views.production_dashboard_view, name="production-dashboard"),
]
