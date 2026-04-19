from django.contrib import admin

from finance.models import Invoice, OpeningBalance, Payment


@admin.register(OpeningBalance)
class OpeningBalanceAdmin(admin.ModelAdmin):
    list_display = ("effective_date", "party", "balance_type", "amount", "source_batch")
    list_filter = ("balance_type", "effective_date")
    search_fields = ("party__name", "remarks")
    autocomplete_fields = ("party",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_date", "invoice_number", "party", "amount", "source_batch")
    list_filter = ("invoice_date",)
    search_fields = ("invoice_number", "party__name", "remarks")
    autocomplete_fields = ("party",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_date", "party", "amount", "mode", "reference_number", "source_batch")
    list_filter = ("payment_date", "mode")
    search_fields = ("reference_number", "party__name", "remarks")
    autocomplete_fields = ("party",)
