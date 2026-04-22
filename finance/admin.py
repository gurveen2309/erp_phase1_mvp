from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from finance.models import Invoice, OpeningBalance, Payment
from governance.admin_mixins import FinanceApprovalAdminMixin
from reporting.admin_mixins import ReceiptAdminMixin


@admin.register(OpeningBalance)
class OpeningBalanceAdmin(FinanceApprovalAdminMixin, admin.ModelAdmin):
    list_display = ("effective_date", "party", "balance_type", "amount")
    list_filter = ("balance_type", "effective_date")
    search_fields = ("party__name", "remarks")
    autocomplete_fields = ("party",)


@admin.register(Invoice)
class InvoiceAdmin(ReceiptAdminMixin, admin.ModelAdmin):
    receipt_url_name = "reporting:invoice-receipt-pdf"
    list_display = ("invoice_date", "invoice_number", "receipt_code_display", "party", "amount")
    list_filter = ("invoice_date", ("party", admin.RelatedOnlyFieldListFilter))
    search_fields = ("invoice_number", "=id", "party__name", "remarks")
    autocomplete_fields = ("party",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "party",
                    "invoice_number",
                    "invoice_date",
                    "amount",
                    "remarks",
                    "receipt_code_display",
                    "receipt_generated_at",
                    "receipt_download_link",
                )
            },
        ),
        (
            "Report Details",
            {
                "fields": (
                    "report_date",
                    "part_name",
                )
            },
        ),
        (
            "Process Report",
            {
                "fields": (
                    "process_report_reference",
                    "process_report_pdf",
                    "process_report_template_link",
                    "process_report_uploaded_link",
                )
            },
        ),
        (
            "Inspection Report",
            {
                "fields": (
                    "inspection_report_reference",
                    "inspection_report_pdf",
                    "inspection_report_template_link",
                    "inspection_report_uploaded_link",
                )
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        readonly_fields.extend(
            [
                "process_report_reference",
                "process_report_template_link",
                "process_report_uploaded_link",
                "inspection_report_reference",
                "inspection_report_template_link",
                "inspection_report_uploaded_link",
            ]
        )
        return readonly_fields

    def process_report_reference(self, obj):
        return obj.receipt_code() if obj and obj.pk else "-"

    process_report_reference.short_description = "Report Number"

    def process_report_template_link(self, obj):
        if not obj or not obj.pk:
            return "Save the invoice first."
        return format_html(
            '<a href="{}" target="_blank">Download Process Report Template</a>',
            reverse("reporting:invoice-process-template-pdf", args=[obj.pk]),
        )

    process_report_template_link.short_description = "Template PDF"

    def process_report_uploaded_link(self, obj):
        if not obj or not obj.pk or not obj.process_report_pdf:
            return "Not uploaded"
        return format_html(
            '<a href="{}" target="_blank">Download Uploaded Process Report</a>',
            reverse("reporting:invoice-process-uploaded-pdf", args=[obj.pk]),
        )

    process_report_uploaded_link.short_description = "Uploaded PDF"

    def inspection_report_reference(self, obj):
        return obj.receipt_code() if obj and obj.pk else "-"

    inspection_report_reference.short_description = "Report Number"

    def inspection_report_template_link(self, obj):
        if not obj or not obj.pk:
            return "Save the invoice first."
        return format_html(
            '<a href="{}" target="_blank">Download Inspection Report Template</a>',
            reverse("reporting:invoice-inspection-template-pdf", args=[obj.pk]),
        )

    inspection_report_template_link.short_description = "Template PDF"

    def inspection_report_uploaded_link(self, obj):
        if not obj or not obj.pk or not obj.inspection_report_pdf:
            return "Not uploaded"
        return format_html(
            '<a href="{}" target="_blank">Download Uploaded Inspection Report</a>',
            reverse("reporting:invoice-inspection-uploaded-pdf", args=[obj.pk]),
        )

    inspection_report_uploaded_link.short_description = "Uploaded PDF"


@admin.register(Payment)
class PaymentAdmin(FinanceApprovalAdminMixin, admin.ModelAdmin):
    list_display = ("payment_date", "party", "amount", "mode", "reference_number")
    list_filter = ("payment_date", "mode", ("party", admin.RelatedOnlyFieldListFilter))
    search_fields = ("reference_number", "party__name", "remarks")
    autocomplete_fields = ("party",)
