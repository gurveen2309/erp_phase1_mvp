from django.contrib import admin

from production.models import Challan
from reporting.admin_mixins import ReceiptAdminMixin


@admin.register(Challan)
class ChallanAdmin(ReceiptAdminMixin, admin.ModelAdmin):
    receipt_url_name = "reporting:challan-receipt-pdf"
    list_display = (
        "challan_date",
        "challan_number",
        "receipt_code_display",
        "party",
        "job_description",
        "direction",
        "weight_kg",
        "amount",
    )
    list_filter = ("direction", "challan_date", ("party", admin.RelatedOnlyFieldListFilter))
    search_fields = ("challan_number", "=id", "party__name", "job_description", "job_type")
    autocomplete_fields = ("party",)
