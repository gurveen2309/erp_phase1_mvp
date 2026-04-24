from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

from finance.models import Invoice
from finance.services import monthly_invoice_summary, outstanding_summary, party_ledger, production_summary, top_parties
from production.models import Challan
from reporting.forms import DateRangeForm, LedgerFilterForm
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
