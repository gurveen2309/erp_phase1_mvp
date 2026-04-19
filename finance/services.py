from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import Coalesce, TruncMonth

from finance.models import Invoice, OpeningBalance, Payment
from masters.models import Party
from production.models import Challan


ZERO = Decimal("0.00")


@dataclass
class LedgerEntry:
    entry_date: date
    event_type: str
    document_no: str
    particulars: str
    debit: Decimal
    credit: Decimal
    running_balance: Decimal


def signed_opening_balance(record: OpeningBalance) -> Decimal:
    return record.amount if record.balance_type == OpeningBalance.BalanceType.DEBIT else record.amount * Decimal("-1")


def party_ledger(party: Party, start_date: date | None = None, end_date: date | None = None) -> list[LedgerEntry]:
    items: list[tuple[date, int, str, str, Decimal, Decimal]] = []

    opening_balances = party.opening_balances.all()
    invoices = party.invoices.all()
    payments = party.payments.all()

    if start_date:
        opening_balances = opening_balances.filter(effective_date__gte=start_date)
        invoices = invoices.filter(invoice_date__gte=start_date)
        payments = payments.filter(payment_date__gte=start_date)
    if end_date:
        opening_balances = opening_balances.filter(effective_date__lte=end_date)
        invoices = invoices.filter(invoice_date__lte=end_date)
        payments = payments.filter(payment_date__lte=end_date)

    for balance in opening_balances.order_by("effective_date", "id"):
        signed_amount = signed_opening_balance(balance)
        items.append(
            (
                balance.effective_date,
                0,
                "",
                balance.remarks or "Opening balance",
                signed_amount if signed_amount > 0 else ZERO,
                abs(signed_amount) if signed_amount < 0 else ZERO,
            )
        )

    for invoice in invoices.order_by("invoice_date", "id"):
        document_no = invoice.invoice_number or f"INV-{invoice.id}"
        items.append(
            (
                invoice.invoice_date,
                1,
                document_no,
                invoice.remarks or "Invoice",
                invoice.amount,
                ZERO,
            )
        )

    for payment in payments.order_by("payment_date", "id"):
        document_no = payment.reference_number or f"PAY-{payment.id}"
        items.append(
            (
                payment.payment_date,
                2,
                document_no,
                payment.remarks or f"Payment via {payment.get_mode_display()}",
                ZERO,
                payment.amount,
            )
        )

    running_balance = ZERO
    ledger_entries: list[LedgerEntry] = []
    for entry_date, _, document_no, particulars, debit, credit in sorted(items, key=lambda row: (row[0], row[1], row[2])):
        running_balance += debit
        running_balance -= credit
        ledger_entries.append(
            LedgerEntry(
                entry_date=entry_date,
                event_type="debit" if debit else "credit" if credit else "opening_balance",
                document_no=document_no,
                particulars=particulars,
                debit=debit,
                credit=credit,
                running_balance=running_balance,
            )
        )
    return ledger_entries


def outstanding_summary():
    invoice_totals = Invoice.objects.values("party").annotate(total=Coalesce(Sum("amount"), ZERO))
    payment_totals = Payment.objects.values("party").annotate(total=Coalesce(Sum("amount"), ZERO))
    opening_totals = []
    for item in OpeningBalance.objects.select_related("party"):
        opening_totals.append((item.party_id, signed_opening_balance(item)))

    invoice_map = {row["party"]: row["total"] for row in invoice_totals}
    payment_map = {row["party"]: row["total"] for row in payment_totals}
    opening_map: dict[int, Decimal] = {}
    for party_id, amount in opening_totals:
        opening_map[party_id] = opening_map.get(party_id, ZERO) + amount

    rows = []
    for party in Party.objects.filter(is_active=True).order_by("name"):
        opening_amount = opening_map.get(party.id, ZERO)
        invoice_amount = invoice_map.get(party.id, ZERO)
        payment_amount = payment_map.get(party.id, ZERO)
        outstanding = opening_amount + invoice_amount - payment_amount
        rows.append(
            {
                "party": party,
                "opening_balance": opening_amount,
                "invoice_total": invoice_amount,
                "payment_total": payment_amount,
                "outstanding": outstanding,
            }
        )
    return rows


def production_summary(start_date: date | None = None, end_date: date | None = None):
    challans = Challan.objects.all()
    if start_date:
        challans = challans.filter(challan_date__gte=start_date)
    if end_date:
        challans = challans.filter(challan_date__lte=end_date)

    return challans.values("challan_date").annotate(
        total_challans=Count("id"),
        total_weight=Coalesce(Sum("weight_kg"), ZERO),
        total_amount=Coalesce(Sum("amount"), ZERO),
    ).order_by("-challan_date")


def monthly_invoice_summary():
    return (
        Invoice.objects.annotate(month=TruncMonth("invoice_date"))
        .values("month")
        .annotate(total_amount=Coalesce(Sum("amount"), ZERO))
        .order_by("-month")
    )


def top_parties(limit: int = 10):
    return (
        Invoice.objects.values("party__name")
        .annotate(total_amount=Coalesce(Sum("amount"), ZERO))
        .order_by("-total_amount", "party__name")[:limit]
    )
