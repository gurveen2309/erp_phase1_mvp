from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from finance.services import monthly_invoice_summary, outstanding_summary, party_ledger, production_summary, top_parties
from reporting.forms import DateRangeForm, LedgerFilterForm


@staff_member_required
def party_ledger_view(request):
    form = LedgerFilterForm(request.GET or None)
    entries = []
    selected_party = None
    if form.is_valid():
        selected_party = form.cleaned_data["party"]
        entries = party_ledger(
            selected_party,
            start_date=form.cleaned_data.get("start_date"),
            end_date=form.cleaned_data.get("end_date"),
        )
    return render(
        request,
        "reporting/party_ledger.html",
        {
            "form": form,
            "entries": entries,
            "selected_party": selected_party,
        },
    )


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
