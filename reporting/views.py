from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.base import ContentFile
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from finance.models import Invoice
from finance.services import monthly_invoice_summary, outstanding_summary, party_ledger, production_summary, top_parties
from production.models import Challan, InspectionReport, ProcessReport
from reporting.forms import DateRangeForm, InspectionReportForm, LedgerFilterForm, ProcessReportForm
from reporting.pdf_exports import (
    build_blank_inspection_template_pdf,
    build_blank_process_template_pdf,
    build_document_receipt_pdf,
    build_party_ledger_pdf,
)


@staff_member_required
def home_view(request):
    return render(request, "reporting/home.html")


@staff_member_required
def blank_templates_view(request):
    return render(request, "reporting/templates_library.html")


@staff_member_required
def blank_process_template_pdf_view(request):
    pdf_bytes = build_blank_process_template_pdf()
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="heat_treatment_process_template.pdf"'
    return response


@staff_member_required
def blank_inspection_template_pdf_view(request):
    pdf_bytes = build_blank_inspection_template_pdf()
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="heat_treatment_inspection_template.pdf"'
    return response


def _save_report_pdf(report, pdf_bytes: bytes, prefix: str) -> str:
    print("Saving report PDF...")
    report.save()
    filename = f"{prefix}_{report.party_id}_{timezone.now():%Y%m%d_%H%M%S}.pdf"
    print("Saving report PDF with filename:", filename)
    report.pdf.save(filename, ContentFile(pdf_bytes), save=True)
    report.refresh_from_db()
    print("Report saved with PDF:", report.pdf.name)
    return report.pdf.name


@staff_member_required
def process_report_form_view(request):
    initial = {}
    invoice_id = request.GET.get("invoice_id")
    if invoice_id:
        invoice = get_object_or_404(Invoice.objects.select_related("party"), pk=invoice_id)
        initial["party"] = invoice.party_id
        initial["invoice"] = invoice.pk

    if request.method == "POST":
        form = ProcessReportForm(request.POST)
        if form.is_valid():
            data = dict(form.cleaned_data)
            party = data.pop("party")
            invoice = data.pop("invoice", None)

            pdf_ctx = {**data, "customer_name": party.name}
            pdf_bytes = build_blank_process_template_pdf(extra_context=pdf_ctx)

            report = ProcessReport(
                party=party,
                invoice=invoice,
                generated_by=request.user,
                **data,
            )
            print("*"*100)
            print("Report data:", data)
            print("Report:", report)
            print("PDF BYTES:", pdf_bytes)
            filename = _save_report_pdf(report, pdf_bytes, "process")
            print("Saved report PDF with filename:", filename)
            if invoice:
                invoice.process_report_pdf.save(filename, ContentFile(pdf_bytes), save=True)

            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="process_report.pdf"'
            return response
    else:
        form = ProcessReportForm(initial=initial)

    return render(request, "reporting/process_report_form.html", {"form": form})


@staff_member_required
def inspection_report_form_view(request):
    initial = {}
    invoice_id = request.GET.get("invoice_id")
    if invoice_id:
        invoice = get_object_or_404(Invoice.objects.select_related("party"), pk=invoice_id)
        initial["party"] = invoice.party_id
        initial["invoice"] = invoice.pk

    if request.method == "POST":
        form = InspectionReportForm(request.POST)
        if form.is_valid():
            data = dict(form.cleaned_data)
            party = data.pop("party")
            invoice = data.pop("invoice", None)

            pdf_ctx = {**data, "customer": party.name}
            pdf_bytes = build_blank_inspection_template_pdf(extra_context=pdf_ctx)

            report = InspectionReport(
                party=party,
                invoice=invoice,
                generated_by=request.user,
                **data,
            )
            filename = _save_report_pdf(report, pdf_bytes, "inspection")
            if invoice:
                invoice.inspection_report_pdf.save(filename, ContentFile(pdf_bytes), save=True)

            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="inspection_report.pdf"'
            return response
    else:
        form = InspectionReportForm(initial=initial)

    return render(request, "reporting/inspection_report_form.html", {"form": form})


@staff_member_required
def report_history_view(request):
    party_id = request.GET.get("party")
    process_qs = ProcessReport.objects.select_related("party", "invoice", "generated_by")
    inspection_qs = InspectionReport.objects.select_related("party", "invoice", "generated_by")
    if party_id:
        process_qs = process_qs.filter(party_id=party_id)
        inspection_qs = inspection_qs.filter(party_id=party_id)

    rows = []
    for r in process_qs:
        rows.append({"kind": "Process", "obj": r})
    for r in inspection_qs:
        rows.append({"kind": "Inspection", "obj": r})
    rows.sort(key=lambda x: x["obj"].generated_at, reverse=True)

    return render(request, "reporting/report_history.html", {"rows": rows})


@staff_member_required
def party_ledger_view(request):
    form = LedgerFilterForm(request.GET or None)
    entries = []
    selected_party = None
    export_query = ""
    if form.is_valid():
        selected_party = form.cleaned_data["party"]
        entries = party_ledger(
            selected_party,
            start_date=form.cleaned_data.get("start_date"),
            end_date=form.cleaned_data.get("end_date"),
        )
        export_query = request.GET.urlencode()
    return render(
        request,
        "reporting/party_ledger.html",
        {
            "form": form,
            "entries": entries,
            "selected_party": selected_party,
            "export_query": export_query,
        },
    )


@staff_member_required
def party_ledger_pdf_view(request):
    form = LedgerFilterForm(request.GET or None)
    if not form.is_valid():
        return HttpResponse("A valid party selection is required to generate the statement PDF.", status=400)

    selected_party = form.cleaned_data["party"]
    start_date = form.cleaned_data.get("start_date")
    end_date = form.cleaned_data.get("end_date")
    entries = party_ledger(selected_party, start_date=start_date, end_date=end_date)
    pdf_bytes = build_party_ledger_pdf(
        party=selected_party,
        entries=entries,
        start_date=start_date,
        end_date=end_date,
    )
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    safe_name = selected_party.name.replace("/", "-").replace(" ", "_")
    response["Content-Disposition"] = f'attachment; filename="{safe_name}_ledger_statement.pdf"'
    return response


@staff_member_required
def challan_receipt_pdf_view(request, challan_id: int):
    challan = get_object_or_404(Challan.objects.select_related("party"), pk=challan_id)
    pdf_bytes = build_document_receipt_pdf(
        document_type="Challan",
        receipt_code=challan.receipt_code(),
        party_name=challan.party.name,
        document_number=challan.challan_number,
        document_date=challan.challan_date,
        amount=challan.amount,
        receipt_generated_at=challan.receipt_generated_at,
        weight_kg=challan.weight_kg,
    )
    filename = challan.receipt_code().replace("/", "-")
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}_receipt.pdf"'
    return response


@staff_member_required
def invoice_receipt_pdf_view(request, invoice_id: int):
    invoice = get_object_or_404(Invoice.objects.select_related("party"), pk=invoice_id)
    pdf_bytes = build_document_receipt_pdf(
        document_type="Invoice",
        receipt_code=invoice.receipt_code(),
        party_name=invoice.party.name,
        document_number=invoice.invoice_number,
        document_date=invoice.invoice_date,
        amount=invoice.amount,
        receipt_generated_at=invoice.receipt_generated_at,
    )
    filename = invoice.receipt_code().replace("/", "-")
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}_receipt.pdf"'
    return response


@staff_member_required
def invoice_process_uploaded_pdf_view(request, invoice_id: int):
    invoice = get_object_or_404(Invoice.objects.select_related("party"), pk=invoice_id)
    if not invoice.process_report_pdf:
        raise Http404("Process report PDF has not been uploaded.")
    response = FileResponse(invoice.process_report_pdf.open("rb"), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{invoice.receipt_code()}_process_report.pdf"'
    return response


@staff_member_required
def invoice_inspection_uploaded_pdf_view(request, invoice_id: int):
    invoice = get_object_or_404(Invoice.objects.select_related("party"), pk=invoice_id)
    if not invoice.inspection_report_pdf:
        raise Http404("Inspection report PDF has not been uploaded.")
    response = FileResponse(invoice.inspection_report_pdf.open("rb"), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{invoice.receipt_code()}_inspection_report.pdf"'
    return response


@staff_member_required
def outstanding_summary_view(request):
    return render(
        request,
        "reporting/outstanding_summary.html",
        {
            "rows": outstanding_summary(),
        },
    )


@staff_member_required
def production_dashboard_view(request):
    form = DateRangeForm(request.GET or None)
    daily_rows = []
    if form.is_valid():
        daily_rows = production_summary(
            start_date=form.cleaned_data.get("start_date"),
            end_date=form.cleaned_data.get("end_date"),
        )
    return render(
        request,
        "reporting/production_dashboard.html",
        {
            "form": form,
            "daily_rows": daily_rows,
            "monthly_rows": monthly_invoice_summary(),
            "top_party_rows": top_parties(),
        },
    )
