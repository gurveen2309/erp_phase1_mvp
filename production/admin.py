import zipfile
from io import BytesIO

from django.contrib import admin
from django.http import HttpResponse

from production.models import Challan, InspectionReport, ProcessReport
from reporting.admin_mixins import ReceiptAdminMixin


def _download_pdfs(queryset, zip_name):
    print("Queryset:", queryset)
    print("ZIP NAME:", zip_name)
    records = [(r, r.pdf) for r in queryset if r.pdf]
    if not records:
        return HttpResponse("No PDFs found for selected records.", status=404)
    if len(records) == 1:
        _, pdf_field = records[0]
        response = HttpResponse(pdf_field.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{pdf_field.name.split("/")[-1]}"'
        return response
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for _, pdf_field in records:
            zf.writestr(pdf_field.name.split("/")[-1], pdf_field.read())
    buf.seek(0)
    response = HttpResponse(buf, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{zip_name}"'
    return response


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


@admin.register(ProcessReport)
class ProcessReportAdmin(admin.ModelAdmin):
    list_display = ("id", "generated_at", "party", "invoice", "part_name", "ref_no", "generated_by")
    list_filter = ("generated_at", ("party", admin.RelatedOnlyFieldListFilter))
    search_fields = ("=id", "party__name", "ref_no", "part_name", "sample_id")
    autocomplete_fields = ("party", "invoice")
    readonly_fields = ("generated_at", "generated_by", "pdf")
    date_hierarchy = "generated_at"
    actions = ["download_pdfs"]

    @admin.action(description="Download PDF(s)")
    def download_pdfs(self, request, queryset):
        return _download_pdfs(queryset, "process_reports.zip")


@admin.register(InspectionReport)
class InspectionReportAdmin(admin.ModelAdmin):
    list_display = ("id", "generated_at", "party", "invoice", "part_name", "no", "generated_by")
    list_filter = ("generated_at", ("party", admin.RelatedOnlyFieldListFilter))
    search_fields = ("=id", "party__name", "no", "part_name")
    autocomplete_fields = ("party", "invoice")
    readonly_fields = ("generated_at", "generated_by", "pdf")
    date_hierarchy = "generated_at"
    actions = ["download_pdfs"]

    @admin.action(description="Download PDF(s)")
    def download_pdfs(self, request, queryset):
        return _download_pdfs(queryset, "inspection_reports.zip")
