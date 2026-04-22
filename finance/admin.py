from django.contrib import admin

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
class InvoiceAdmin(ReceiptAdminMixin, FinanceApprovalAdminMixin, admin.ModelAdmin):
    receipt_url_name = "reporting:invoice-receipt-pdf"
    list_display = ("invoice_date", "invoice_number", "receipt_code_display", "party", "amount")
    list_filter = ("invoice_date", ("party", admin.RelatedOnlyFieldListFilter))
    search_fields = ("invoice_number", "=id", "party__name", "remarks")
    autocomplete_fields = ("party",)


@admin.register(Payment)
class PaymentAdmin(FinanceApprovalAdminMixin, admin.ModelAdmin):
    list_display = ("payment_date", "party", "amount", "mode", "reference_number")
    list_filter = ("payment_date", "mode", ("party", admin.RelatedOnlyFieldListFilter))
    search_fields = ("reference_number", "party__name", "remarks")
    autocomplete_fields = ("party",)
