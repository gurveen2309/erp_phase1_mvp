from __future__ import annotations

import io
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.template.loader import render_to_string
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A6
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from weasyprint import HTML

from finance.services import LedgerEntry
from masters.models import Party


PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 12 * mm
RIGHT_MARGIN = 12 * mm
TOP_MARGIN = 14 * mm
BOTTOM_MARGIN = 12 * mm
ROW_HEIGHT = 7 * mm


def _render_html_pdf(template_name: str, context: dict) -> bytes:
    html = render_to_string(template_name, context)
    return HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()


def _blank_template_context() -> dict:
    return {
        "company_name": settings.ERP_COMPANY_NAME,
        "company_address_lines": [line.strip() for line in settings.ERP_COMPANY_MAIN_ADDRESS.splitlines() if line.strip()],
        "company_gstin": settings.ERP_COMPANY_GSTIN,
    }


def _format_statement_date(value: date | None) -> str:
    return value.strftime("%d/%b/%Y") if value else ""


def _format_period_date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else ""


def _format_datetime(value) -> str:
    return value.strftime("%d/%m/%Y %H:%M") if value else ""


def _format_amount(value: Decimal) -> str:
    if not value:
        return ""
    return f"{value:.2f}"


def _balance_dc(value: Decimal) -> tuple[str, str]:
    if value > 0:
        return "DR", f"{abs(value):.2f}"
    if value < 0:
        return "CR", f"{abs(value):.2f}"
    return "", "0.00"


def _statement_period(entries: list[LedgerEntry], start_date: date | None, end_date: date | None) -> tuple[date | None, date | None]:
    resolved_start = start_date or (entries[0].entry_date if entries else None)
    resolved_end = end_date or (entries[-1].entry_date if entries else None)
    return resolved_start, resolved_end


def _draw_header(pdf: canvas.Canvas, party: Party, start_date: date | None, end_date: date | None) -> float:
    company_name = settings.ERP_COMPANY_NAME
    company_address = settings.ERP_COMPANY_ADDRESS
    company_gstin = settings.ERP_COMPANY_GSTIN

    y = PAGE_HEIGHT - TOP_MARGIN
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(LEFT_MARGIN, y, company_name)

    y -= 7 * mm
    if company_address:
        pdf.setFont("Helvetica", 9)
        for line in [line.strip() for line in company_address.splitlines() if line.strip()]:
            pdf.drawString(LEFT_MARGIN, y, line)
            y -= 4.5 * mm
    else:
        y -= 1 * mm

    if company_gstin:
        pdf.setFont("Helvetica", 9)
        pdf.drawString(LEFT_MARGIN, y, f"GSTIN : {company_gstin}")
        y -= 6 * mm

    pdf.setFont("Helvetica-Bold", 10)
    title = f"{party.name} FROM {_format_period_date(start_date)} TO {_format_period_date(end_date)}".strip()
    pdf.drawString(LEFT_MARGIN, y, title)
    return y - 6 * mm


def _receipt_header(pdf: canvas.Canvas, page_width: float, top_y: float) -> float:
    company_name = settings.ERP_COMPANY_NAME
    company_address = settings.ERP_COMPANY_ADDRESS
    company_gstin = settings.ERP_COMPANY_GSTIN

    y = top_y
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(10 * mm, y, company_name)
    y -= 5 * mm

    if company_address:
        pdf.setFont("Helvetica", 8)
        for line in [line.strip() for line in company_address.splitlines() if line.strip()]:
            pdf.drawString(10 * mm, y, line)
            y -= 4 * mm

    if company_gstin:
        pdf.setFont("Helvetica", 8)
        pdf.drawString(10 * mm, y, f"GSTIN: {company_gstin}")
        y -= 5 * mm

    pdf.setStrokeColor(colors.black)
    pdf.line(10 * mm, y, page_width - 10 * mm, y)
    return y - 5 * mm


def _draw_table_header(pdf: canvas.Canvas, y: float) -> float:
    x_positions = {
        "date": LEFT_MARGIN,
        "particulars": LEFT_MARGIN + 28 * mm,
        "debit": LEFT_MARGIN + 110 * mm,
        "credit": LEFT_MARGIN + 138 * mm,
        "dc": LEFT_MARGIN + 166 * mm,
        "balance": LEFT_MARGIN + 180 * mm,
    }
    pdf.setStrokeColor(colors.black)
    pdf.line(LEFT_MARGIN, y, PAGE_WIDTH - RIGHT_MARGIN, y)
    y -= 5 * mm
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(x_positions["date"], y, "DATE")
    pdf.drawString(x_positions["particulars"], y, "PARTICULARS")
    pdf.drawRightString(x_positions["debit"] + 18 * mm, y, "DEBIT")
    pdf.drawRightString(x_positions["credit"] + 18 * mm, y, "CREDIT")
    pdf.drawString(x_positions["dc"], y, "D/C")
    pdf.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, y, "BALANCE")
    y -= 2 * mm
    pdf.line(LEFT_MARGIN, y, PAGE_WIDTH - RIGHT_MARGIN, y)
    return y - 5 * mm


def _draw_footer(pdf: canvas.Canvas) -> None:
    pdf.setFont("Helvetica", 8)
    pdf.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, 8 * mm, f"Generated from ERP on {date.today():%d/%m/%Y}")


def _draw_totals(pdf: canvas.Canvas, y: float, entries: list[LedgerEntry]) -> float:
    total_debit = sum((entry.debit for entry in entries), Decimal("0.00"))
    total_credit = sum((entry.credit for entry in entries), Decimal("0.00"))
    closing_balance = entries[-1].running_balance if entries else Decimal("0.00")
    balance_dc, balance_value = _balance_dc(closing_balance)

    if y <= BOTTOM_MARGIN + 12 * mm:
        _draw_footer(pdf)
        pdf.showPage()
        y = PAGE_HEIGHT - TOP_MARGIN - 10 * mm

    pdf.line(LEFT_MARGIN, y + 2 * mm, PAGE_WIDTH - RIGHT_MARGIN, y + 2 * mm)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(LEFT_MARGIN + 28 * mm, y - 4 * mm, "TOTAL")
    pdf.drawRightString(LEFT_MARGIN + 128 * mm, y - 4 * mm, _format_amount(total_debit))
    pdf.drawRightString(LEFT_MARGIN + 156 * mm, y - 4 * mm, _format_amount(total_credit))
    pdf.drawString(LEFT_MARGIN + 166 * mm, y - 4 * mm, balance_dc)
    pdf.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, y - 4 * mm, balance_value)
    pdf.line(LEFT_MARGIN, y - 7 * mm, PAGE_WIDTH - RIGHT_MARGIN, y - 7 * mm)
    return y - 9 * mm


def build_party_ledger_pdf(*, party: Party, entries: list[LedgerEntry], start_date: date | None = None, end_date: date | None = None) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"{party.name} Ledger Statement")

    resolved_start, resolved_end = _statement_period(entries, start_date, end_date)
    y = _draw_header(pdf, party, resolved_start, resolved_end)
    y = _draw_table_header(pdf, y)

    for entry in entries:
        if y <= BOTTOM_MARGIN + 12 * mm:
            _draw_footer(pdf)
            pdf.showPage()
            y = _draw_header(pdf, party, resolved_start, resolved_end)
            y = _draw_table_header(pdf, y)

        balance_dc, balance_value = _balance_dc(entry.running_balance)
        pdf.setFont("Helvetica", 8)
        pdf.drawString(LEFT_MARGIN, y, _format_statement_date(entry.entry_date))
        pdf.drawString(LEFT_MARGIN + 28 * mm, y, (entry.particulars or "")[:48])
        pdf.drawRightString(LEFT_MARGIN + 128 * mm, y, _format_amount(entry.debit))
        pdf.drawRightString(LEFT_MARGIN + 156 * mm, y, _format_amount(entry.credit))
        pdf.drawString(LEFT_MARGIN + 166 * mm, y, balance_dc)
        pdf.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, y, balance_value)
        y -= ROW_HEIGHT

    y = _draw_totals(pdf, y, entries)
    _draw_footer(pdf)
    pdf.save()
    return buffer.getvalue()


def build_document_receipt_pdf(
    *,
    document_type: str,
    receipt_code: str,
    party_name: str,
    document_number: str,
    document_date: date,
    amount: Decimal,
    receipt_generated_at,
    weight_kg: Decimal | None = None,
) -> bytes:
    page_width, page_height = A6
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A6)
    pdf.setTitle(f"{receipt_code} {document_type} Receipt")

    y = _receipt_header(pdf, page_width, page_height - 10 * mm)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(10 * mm, y, f"{document_type} RECEIPT")
    y -= 6 * mm

    rows = [
        ("Receipt ID", receipt_code),
        ("Party", party_name),
        ("Number", document_number or "-"),
        ("Date", _format_period_date(document_date)),
        ("Amount", f"{amount:.2f}"),
    ]
    if weight_kg is not None:
        rows.append(("Weight (kg)", f"{weight_kg:.2f}"))
    rows.append(("Generated", _format_datetime(receipt_generated_at)))

    label_x = 10 * mm
    value_x = 42 * mm
    pdf.setFont("Helvetica", 8.5)
    for label, value in rows:
        pdf.setFillColor(colors.black)
        pdf.drawString(label_x, y, f"{label}:")
        pdf.drawString(value_x, y, str(value))
        y -= 5.5 * mm

    pdf.line(10 * mm, y, page_width - 10 * mm, y)
    y -= 5 * mm
    pdf.setFont("Helvetica", 7.5)
    pdf.drawString(10 * mm, y, "Attach this slip to the physical document for ERP reference.")

    pdf.save()
    return buffer.getvalue()


def build_blank_process_template_pdf(extra_context: dict | None = None) -> bytes:
    ctx = _blank_template_context()
    if extra_context:
        ctx.update(extra_context)
    return _render_html_pdf("reporting/pdf/process_report_template.html", ctx)


def build_blank_inspection_template_pdf(extra_context: dict | None = None) -> bytes:
    ctx = _blank_template_context()
    if extra_context:
        ctx.update(extra_context)
    return _render_html_pdf("reporting/pdf/inspection_report_template.html", ctx)
