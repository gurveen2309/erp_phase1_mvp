from django.contrib import admin

from masters.models import Party


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "phone", "gst_number", "is_active", "source_batch")
    list_filter = ("is_active",)
    search_fields = ("name", "contact_person", "phone", "gst_number")
