from django.contrib import admin

from production.models import Challan


@admin.register(Challan)
class ChallanAdmin(admin.ModelAdmin):
    list_display = ("challan_date", "challan_number", "party", "job_description", "direction", "weight_kg", "amount")
    list_filter = ("direction", "challan_date")
    search_fields = ("challan_number", "party__name", "job_description", "job_type")
    autocomplete_fields = ("party",)
