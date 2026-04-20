from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import render

from finance.services import monthly_invoice_summary, outstanding_summary, party_ledger, production_summary, top_parties
from reporting.forms import DateRangeForm, LedgerFilterForm
from reporting.pdf_exports import build_party_ledger_pdf


@staff_member_required
def home_view(request):
    return render(request, "reporting/home.html")


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
