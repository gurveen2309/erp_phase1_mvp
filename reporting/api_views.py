from __future__ import annotations

from django.http import JsonResponse

from finance.services import monthly_invoice_summary, production_summary, top_parties


def production_daily_api(request):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    rows = production_summary(start_date=start_date, end_date=end_date)
    data = [
        {
            "date": str(row["challan_date"]),
            "total_challans": row["total_challans"],
            "total_weight": float(row["total_weight"]),
            "amount": float(row["total_amount"]),
        }
        for row in rows
    ]
    return JsonResponse(data, safe=False)


def monthly_summary_api(request):
    rows = monthly_invoice_summary()
    data = [
        {
            "month": row["month"].strftime("%Y-%m") if row["month"] else None,
            "total_amount": float(row["total_amount"]),
        }
        for row in rows
    ]
    return JsonResponse(data, safe=False)


def top_parties_api(request):
    rows = top_parties()
    data = [
        {
            "party_name": row["party__name"],
            "total_amount": float(row["total_amount"]),
        }
        for row in rows
    ]
    # Calculate percentages
    grand_total = sum(d["total_amount"] for d in data) or 1
    for d in data:
        d["percentage"] = round(d["total_amount"] / grand_total * 100, 2)
    return JsonResponse(data, safe=False)
