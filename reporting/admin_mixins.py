from __future__ import annotations

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html


class ReceiptAdminMixin:
    change_form_template = "admin/receipt_change_form.html"
    receipt_url_name = ""

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        for field_name in ("receipt_code_display", "receipt_generated_at", "receipt_download_link"):
            if field_name not in readonly_fields:
                readonly_fields.append(field_name)
        return readonly_fields

    def receipt_code_display(self, obj):
        if not obj or not obj.pk:
            return "-"
        return obj.receipt_code()

    receipt_code_display.short_description = "Receipt Code"

    def receipt_download_link(self, obj):
        if not obj or not obj.pk:
            return "-"
        return format_html(
            '<a href="{}" target="_blank">Download Receipt PDF</a>',
            reverse(self.receipt_url_name, args=[obj.pk]),
        )

    receipt_download_link.short_description = "Receipt PDF"

    def response_add(self, request, obj, post_url_continue=None):
        if "_save_and_download_receipt" in request.POST and obj.pk:
            return HttpResponseRedirect(reverse(self.receipt_url_name, args=[obj.pk]))
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if "_save_and_download_receipt" in request.POST and obj.pk:
            return HttpResponseRedirect(reverse(self.receipt_url_name, args=[obj.pk]))
        return super().response_change(request, obj)
