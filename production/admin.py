import zipfile
from io import BytesIO

from django.contrib import admin
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.utils import timezone

from production.models import Challan, InspectionReport, ProcessReport
from reporting.admin_mixins import ReceiptAdminMixin
from reporting.pdf_exports import build_blank_inspection_template_pdf, build_blank_process_template_pdf


def _download_pdfs(queryset, zip_name):
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


def _save_regenerated_pdf(report, pdf_bytes: bytes, prefix: str) -> None:
    filename = f"{prefix}_{report.party_id}_{report.pk}_{timezone.now():%Y%m%d_%H%M%S}.pdf"
    report.pdf.save(filename, ContentFile(pdf_bytes), save=True)


def _process_report_context(report: ProcessReport) -> dict:
    return {
        "report_title": "Process Report",
        "report_subtitle": "Heat Treatment",
        "ref_no": report.ref_no,
        "dated": report.dated.strftime("%d/%m/%Y") if report.dated else "",
        "date": report.date.strftime("%d/%m/%Y") if report.date else "",
        "customer_name": report.party.name,
        "part_name": report.part_name,
        "hardness": report.hardness,
        "sample_id": report.sample_id,
        "material_grade": report.material_grade,
        "size": report.size,
        "hardening_temp": report.hardening_temp,
        "hardening_speed": report.hardening_speed,
        "hardening_hrc": report.hardening_hrc,
        "quenching_media": report.quenching_media,
        "quenching_temp": report.quenching_temp,
        "tempering_temp": report.tempering_temp,
        "tempering_speed": report.tempering_speed,
        "tempering_hrc": report.tempering_hrc,
    }


def _inspection_report_context(report: InspectionReport) -> dict:
    return {
        "date": report.date.strftime("%d/%m/%Y") if report.date else "",
        "part_name": report.part_name,
        "customer": report.party.name,
        "no": report.no,
        "lot_qty": report.lot_qty,
        "material_grade": report.material_grade,
        "supplier_tc_received": report.supplier_tc_received,
        "process_done": report.process_done,
        "ht": report.ht,
        "hardness_spec": report.hardness_spec,
        "micro_structure_spec": report.micro_structure_spec,
        "grain_size_spec": report.grain_size_spec,
        "tensile_strength_spec": report.tensile_strength_spec,
        "other_requirements_spec": report.other_requirements_spec,
        "hardness_obs_1": report.hardness_obs_1,
        "hardness_obs_2": report.hardness_obs_2,
        "hardness_obs_3": report.hardness_obs_3,
        "hardness_obs_4": report.hardness_obs_4,
        "hardness_obs_5": report.hardness_obs_5,
        "hardness_obs_6": report.hardness_obs_6,
        "hardness_obs_7": report.hardness_obs_7,
        "hardness_obs_8": report.hardness_obs_8,
        "micro_structure_obs_1": report.micro_structure_obs_1,
        "micro_structure_obs_2": report.micro_structure_obs_2,
        "micro_structure_obs_3": report.micro_structure_obs_3,
        "micro_structure_obs_4": report.micro_structure_obs_4,
        "micro_structure_obs_5": report.micro_structure_obs_5,
        "micro_structure_obs_6": report.micro_structure_obs_6,
        "micro_structure_obs_7": report.micro_structure_obs_7,
        "micro_structure_obs_8": report.micro_structure_obs_8,
        "grain_size_obs_1": report.grain_size_obs_1,
        "grain_size_obs_2": report.grain_size_obs_2,
        "grain_size_obs_3": report.grain_size_obs_3,
        "grain_size_obs_4": report.grain_size_obs_4,
        "grain_size_obs_5": report.grain_size_obs_5,
        "grain_size_obs_6": report.grain_size_obs_6,
        "grain_size_obs_7": report.grain_size_obs_7,
        "grain_size_obs_8": report.grain_size_obs_8,
        "tensile_strength_obs_1": report.tensile_strength_obs_1,
        "tensile_strength_obs_2": report.tensile_strength_obs_2,
        "tensile_strength_obs_3": report.tensile_strength_obs_3,
        "tensile_strength_obs_4": report.tensile_strength_obs_4,
        "tensile_strength_obs_5": report.tensile_strength_obs_5,
        "tensile_strength_obs_6": report.tensile_strength_obs_6,
        "tensile_strength_obs_7": report.tensile_strength_obs_7,
        "tensile_strength_obs_8": report.tensile_strength_obs_8,
        "other_obs_1": report.other_obs_1,
        "other_obs_2": report.other_obs_2,
        "other_obs_3": report.other_obs_3,
        "other_obs_4": report.other_obs_4,
        "other_obs_5": report.other_obs_5,
        "other_obs_6": report.other_obs_6,
        "other_obs_7": report.other_obs_7,
        "other_obs_8": report.other_obs_8,
        "qty_checked": report.qty_checked,
        "qty": report.qty,
    }


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
    actions = ["download_pdfs", "regenerate_pdfs"]

    @admin.action(description="Download PDF(s)")
    def download_pdfs(self, request, queryset):
        return _download_pdfs(queryset, "process_reports.zip")

    @admin.action(description="Regenerate PDF(s)")
    def regenerate_pdfs(self, request, queryset):
        count = 0
        for report in queryset:
            pdf_bytes = build_blank_process_template_pdf(extra_context=_process_report_context(report))
            _save_regenerated_pdf(report, pdf_bytes, "process")
            count += 1
        self.message_user(request, f"Regenerated {count} process report PDF(s).")


@admin.register(InspectionReport)
class InspectionReportAdmin(admin.ModelAdmin):
    list_display = ("id", "generated_at", "party", "invoice", "part_name", "no", "generated_by")
    list_filter = ("generated_at", ("party", admin.RelatedOnlyFieldListFilter))
    search_fields = ("=id", "party__name", "no", "part_name")
    autocomplete_fields = ("party", "invoice")
    readonly_fields = ("generated_at", "generated_by", "pdf")
    date_hierarchy = "generated_at"
    actions = ["download_pdfs", "regenerate_pdfs"]

    @admin.action(description="Download PDF(s)")
    def download_pdfs(self, request, queryset):
        return _download_pdfs(queryset, "inspection_reports.zip")

    @admin.action(description="Regenerate PDF(s)")
    def regenerate_pdfs(self, request, queryset):
        count = 0
        for report in queryset:
            pdf_bytes = build_blank_inspection_template_pdf(extra_context=_inspection_report_context(report))
            _save_regenerated_pdf(report, pdf_bytes, "inspection")
            count += 1
        self.message_user(request, f"Regenerated {count} inspection report PDF(s).")
