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


def _format_statement_date(value: date | None) -> str:
    return value.strftime("%d/%b/%Y") if value else ""


def _format_period_date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else ""


def _format_datetime(value) -> str:
    return value.strftime("%d/%m/%Y %H:%M") if value else ""


def _render_html_pdf(template_name: str, context: dict) -> bytes:
    html = render_to_string(template_name, context)
    return HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()


def _report_template_context(*, invoice, report_date: date | None, part_name: str, title: str, subtitle: str) -> dict:
    resolved_report_date = report_date or invoice.invoice_date
    company_address_lines = [line.strip() for line in settings.ERP_COMPANY_ADDRESS.splitlines() if line.strip()]
    return {
        "company_name": settings.ERP_COMPANY_NAME,
        "company_address_lines": company_address_lines,
        "company_gstin": settings.ERP_COMPANY_GSTIN,
        "title": title,
        "subtitle": subtitle,
        "report_no": invoice.receipt_code(),
        "report_date": _format_period_date(resolved_report_date),
        "invoice_no": invoice.invoice_number or "-",
        "invoice_date": _format_period_date(invoice.invoice_date),
        "customer_name": invoice.party.name,
        "part_name": part_name or "-",
    }


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


def _draw_company_banner(pdf: canvas.Canvas, title: str) -> float:
    y = PAGE_HEIGHT - TOP_MARGIN
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(LEFT_MARGIN, y, settings.ERP_COMPANY_NAME)
    y -= 6 * mm

    if settings.ERP_COMPANY_ADDRESS:
        pdf.setFont("Helvetica", 9)
        for line in [line.strip() for line in settings.ERP_COMPANY_ADDRESS.splitlines() if line.strip()]:
            pdf.drawString(LEFT_MARGIN, y, line)
            y -= 4.5 * mm

    if settings.ERP_COMPANY_GSTIN:
        pdf.setFont("Helvetica", 9)
        pdf.drawString(LEFT_MARGIN, y, f"GSTIN: {settings.ERP_COMPANY_GSTIN}")
        y -= 6 * mm

    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(LEFT_MARGIN, y, title)
    y -= 6 * mm
    pdf.line(LEFT_MARGIN, y, PAGE_WIDTH - RIGHT_MARGIN, y)
    return y - 7 * mm


def _draw_label_value_row(pdf: canvas.Canvas, y: float, left_label: str, left_value: str, right_label: str = "", right_value: str = "") -> float:
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(LEFT_MARGIN, y, left_label)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(LEFT_MARGIN + 28 * mm, y, left_value)
    if right_label:
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(LEFT_MARGIN + 100 * mm, y, right_label)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(LEFT_MARGIN + 130 * mm, y, right_value)
    return y - 6 * mm


def _draw_blank_body(pdf: canvas.Canvas, y: float, heading: str, lines: int = 10) -> float:
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(LEFT_MARGIN, y, heading)
    y -= 5 * mm
    pdf.setFont("Helvetica", 8)
    for _ in range(lines):
        pdf.line(LEFT_MARGIN, y, PAGE_WIDTH - RIGHT_MARGIN, y)
        y -= 8 * mm
    return y


def _draw_box(pdf: canvas.Canvas, x: float, y_top: float, width: float, height: float, line_width: float = 1) -> None:
    pdf.setLineWidth(line_width)
    pdf.rect(x, y_top - height, width, height)


def _draw_cell_text(
    pdf: canvas.Canvas,
    x: float,
    y_top: float,
    width: float,
    height: float,
    text: str,
    *,
    font_name: str = "Helvetica",
    font_size: int = 8,
    padding_x: float = 2 * mm,
    padding_y: float = 4 * mm,
    centered: bool = False,
) -> None:
    pdf.setFont(font_name, font_size)
    lines = str(text).splitlines() or [""]
    if centered:
        line_gap = 4 * mm
        start_y = y_top - height / 2 + (len(lines) - 1) * line_gap / 2
        for idx, line in enumerate(lines):
            pdf.drawCentredString(x + width / 2, start_y - idx * line_gap, line)
    else:
        for idx, line in enumerate(lines[:3]):
            pdf.drawString(x + padding_x, y_top - padding_y - idx * 4 * mm, line)


def _draw_company_title_block(pdf: canvas.Canvas, title: str) -> float:
    top = PAGE_HEIGHT - TOP_MARGIN
    left = LEFT_MARGIN
    width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    header_height = 24 * mm
    _draw_box(pdf, left, top, width, header_height)

    pdf.setFont("Helvetica-Bold", 17)
    pdf.drawCentredString(left + width / 2, top - 7 * mm, settings.ERP_COMPANY_NAME)

    info_y = top - 12 * mm
    if settings.ERP_COMPANY_ADDRESS:
        pdf.setFont("Helvetica", 8)
        address = " ".join(line.strip() for line in settings.ERP_COMPANY_ADDRESS.splitlines() if line.strip())
        pdf.drawCentredString(left + width / 2, info_y, address[:120])
        info_y -= 4 * mm

    if settings.ERP_COMPANY_GSTIN:
        pdf.setFont("Helvetica", 8)
        pdf.drawCentredString(left + width / 2, info_y, f"GSTIN: {settings.ERP_COMPANY_GSTIN}")
        info_y -= 4 * mm

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(left + width / 2, top - header_height + 6 * mm, title)
    return top - header_height - 5 * mm


def _draw_process_header_table(pdf: canvas.Canvas, y: float, *, invoice, report_date: date | None, part_name: str) -> float:
    left = LEFT_MARGIN
    width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    row_height = 8 * mm
    label_w = 24 * mm
    value_w = 52 * mm
    right_label_w = 30 * mm
    right_value_w = width - label_w - value_w - right_label_w
    rows = [
        ("Date", _format_period_date(report_date or invoice.invoice_date), "Customer Name", invoice.party.name),
        ("Part Name/No", part_name or "-", "Hardness", ""),
        ("Sample ID No", "", "Material Grade", ""),
    ]
    table_height = row_height * len(rows)
    _draw_box(pdf, left, y, width, table_height)
    x1 = left + label_w
    x2 = x1 + value_w
    x3 = x2 + right_label_w
    pdf.line(x1, y, x1, y - table_height)
    pdf.line(x2, y, x2, y - table_height)
    pdf.line(x3, y, x3, y - table_height)
    for index in range(1, len(rows)):
        pdf.line(left, y - row_height * index, left + width, y - row_height * index)

    row_top = y
    for left_label, left_value, right_label, right_value in rows:
        _draw_cell_text(pdf, left, row_top, label_w, row_height, left_label, font_name="Helvetica-Bold")
        _draw_cell_text(pdf, x1, row_top, value_w, row_height, left_value)
        _draw_cell_text(pdf, x2, row_top, right_label_w, row_height, right_label, font_name="Helvetica-Bold")
        _draw_cell_text(pdf, x3, row_top, right_value_w, row_height, right_value)
        row_top -= row_height
    return y - table_height - 8 * mm


def _draw_process_cycle_table(pdf: canvas.Canvas, y: float) -> float:
    left = LEFT_MARGIN
    width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(left + width / 2, y, "Heat Treatment Cycle")
    y -= 5 * mm
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(left + width / 2, y, "Continuous Furnace")
    y -= 4 * mm

    col_widths = [34 * mm, 22 * mm, 20 * mm, 18 * mm, 22 * mm, 20 * mm, 22 * mm, 20 * mm, 18 * mm]
    scale = width / sum(col_widths)
    col_widths = [w * scale for w in col_widths]
    group_h = 7 * mm
    sub_h = 9 * mm
    body_h = 22 * mm
    total_h = group_h + sub_h + body_h
    _draw_box(pdf, left, y, width, total_h)

    xs = [left]
    for w in col_widths:
        xs.append(xs[-1] + w)
    for x in xs[1:-1]:
        pdf.line(x, y, x, y - total_h)
    pdf.line(left, y - group_h, left + width, y - group_h)
    pdf.line(left, y - group_h - sub_h, left + width, y - group_h - sub_h)

    # Group titles
    _draw_cell_text(pdf, xs[0], y, col_widths[0], group_h + sub_h, "Size", font_name="Helvetica-Bold", centered=True)
    _draw_cell_text(pdf, xs[1], y, col_widths[1] + col_widths[2] + col_widths[3], group_h, "Hardening Process", font_name="Helvetica-Bold", centered=True)
    _draw_cell_text(pdf, xs[4], y, col_widths[4], group_h + sub_h, "Quenching\nMedia", font_name="Helvetica-Bold", centered=True)
    _draw_cell_text(pdf, xs[5], y, col_widths[5], group_h + sub_h, "Quenching\nTemp.", font_name="Helvetica-Bold", centered=True)
    _draw_cell_text(pdf, xs[6], y, col_widths[6] + col_widths[7] + col_widths[8], group_h, "Tempering Process", font_name="Helvetica-Bold", centered=True)

    headers = [
        "",
        "Hardening\nTemp.",
        "Speed\nMesh Belt",
        "Hardening\nHRC",
        "",
        "",
        "Tempering\nTemp.",
        "Speed\nMesh Belt",
        "Tempering\nHRC",
    ]
    row_top = y - group_h
    for idx, header in enumerate(headers):
        if header:
            _draw_cell_text(pdf, xs[idx], row_top, col_widths[idx], sub_h, header, font_name="Helvetica-Bold", centered=True)

    body_top = y - group_h - sub_h
    body_values = ["", "", "", "", "", "", "", "", ""]
    for idx, value in enumerate(body_values):
        _draw_cell_text(pdf, xs[idx], body_top, col_widths[idx], body_h, value, font_size=8)
    return y - total_h - 12 * mm


def _draw_signature_row(pdf: canvas.Canvas, y: float) -> float:
    width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    section_w = width / 2
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(LEFT_MARGIN + 6 * mm, y, "Checked By")
    pdf.drawString(LEFT_MARGIN + section_w + 6 * mm, y, "Approved By")
    pdf.line(LEFT_MARGIN + 6 * mm, y - 10 * mm, LEFT_MARGIN + section_w - 10 * mm, y - 10 * mm)
    pdf.line(LEFT_MARGIN + section_w + 6 * mm, y - 10 * mm, PAGE_WIDTH - RIGHT_MARGIN - 10 * mm, y - 10 * mm)
    return y - 14 * mm


def _draw_inspection_header_block(pdf: canvas.Canvas, y: float, *, invoice, report_date: date | None, part_name: str) -> float:
    left = LEFT_MARGIN
    width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    row_h = 10 * mm
    top_h = 22 * mm
    col1 = 34 * mm
    col3 = 58 * mm
    col2 = width - col1 - col3

    _draw_box(pdf, left, y, width, top_h)
    pdf.line(left + col1, y, left + col1, y - top_h)
    pdf.line(left + col1 + col2, y, left + col1 + col2, y - top_h)
    _draw_cell_text(pdf, left, y, col1, top_h, settings.ERP_COMPANY_NAME, font_name="Helvetica-Bold", font_size=12, centered=True)

    middle_text_y = y - 6 * mm
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawCentredString(left + col1 + col2 / 2, middle_text_y, settings.ERP_COMPANY_NAME)
    pdf.setFont("Helvetica", 8)
    if settings.ERP_COMPANY_ADDRESS:
        address = " ".join(line.strip() for line in settings.ERP_COMPANY_ADDRESS.splitlines() if line.strip())
        pdf.drawCentredString(left + col1 + col2 / 2, middle_text_y - 5 * mm, address[:120])
    _draw_cell_text(pdf, left + col1 + col2, y, col3, top_h, "Heat Treatment Inspection\nReport (Test Certificate)", font_name="Helvetica-Bold", font_size=11, centered=True)
    y -= top_h

    rows = [
        [("DATE", _format_period_date(report_date or invoice.invoice_date), 54 * mm), ("PART NAME", part_name or "-", 72 * mm), ("CUSTOMER", invoice.party.name, 72 * mm), ("NO", invoice.receipt_code(), None)],
        [("LOT QTY", "", 54 * mm), ("MATERIAL GRADE", "", 72 * mm), ("SUPPLIER TC RECEIVED OR NOT", "", None)],
        [("PROCESS DONE", "", width - 34 * mm), ("H/T", "", 34 * mm)],
    ]
    for row in rows:
        row_left = left
        pdf.line(left, y, left + width, y)
        for label, value, fixed_width in row:
            cell_w = fixed_width if fixed_width is not None else (left + width - row_left)
            pdf.line(row_left + cell_w, y, row_left + cell_w, y - row_h)
            _draw_cell_text(pdf, row_left, y, cell_w, row_h, f"{label}: {value}".strip(), font_name="Helvetica-Bold", font_size=8)
            row_left += cell_w
        y -= row_h
    _draw_box(pdf, left, y + row_h * len(rows), width, row_h * len(rows))
    return y


def _draw_inspection_observation_table(pdf: canvas.Canvas, y: float) -> float:
    left = LEFT_MARGIN
    width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    col_widths = [12 * mm, 42 * mm, 32 * mm, 15 * mm, 15 * mm, 15 * mm, 15 * mm, 15 * mm, 15 * mm, 15 * mm, 15 * mm]
    scale = width / sum(col_widths)
    col_widths = [w * scale for w in col_widths]
    header_h = 8 * mm
    body_h = 15 * mm
    rows = [
        ("1", "Hardness(Surface)", ""),
        ("2", "Micro-Structure", ""),
        ("3", "Grain Size", ""),
        ("4", "Tensile Strength (mpa)", ""),
        ("5", "Any Other Requirements", ""),
    ]
    total_h = header_h * 2 + body_h * len(rows) + 12 * mm
    _draw_box(pdf, left, y, width, total_h)

    xs = [left]
    for w in col_widths:
        xs.append(xs[-1] + w)
    for x in xs[1:-1]:
        pdf.line(x, y, x, y - total_h)
    pdf.line(left, y - header_h, left + width, y - header_h)
    pdf.line(xs[3], y - header_h, left + width, y - header_h)

    _draw_cell_text(pdf, xs[0], y, col_widths[0], header_h * 2, "S No.", font_name="Helvetica-Bold", centered=True)
    _draw_cell_text(pdf, xs[1], y, col_widths[1], header_h * 2, "PARAMETERS", font_name="Helvetica-Bold", centered=True)
    _draw_cell_text(pdf, xs[2], y, col_widths[2], header_h * 2, "SPECIFICATIONS", font_name="Helvetica-Bold", centered=True)
    obs_width = sum(col_widths[3:])
    _draw_cell_text(pdf, xs[3], y, obs_width, header_h, "OBSERVATION", font_name="Helvetica-Bold", centered=True)

    second_top = y - header_h
    for idx in range(3, len(col_widths)):
        _draw_cell_text(pdf, xs[idx], second_top, col_widths[idx], header_h, "", centered=True)

    row_top = y - header_h * 2
    for serial, parameter, spec in rows:
        pdf.line(left, row_top, left + width, row_top)
        _draw_cell_text(pdf, xs[0], row_top, col_widths[0], body_h, serial, centered=True)
        _draw_cell_text(pdf, xs[1], row_top, col_widths[1], body_h, parameter, font_name="Helvetica-Bold")
        _draw_cell_text(pdf, xs[2], row_top, col_widths[2], body_h, spec, centered=True)
        row_top -= body_h

    pdf.line(left, row_top, left + width, row_top)
    qty_box_w = 52 * mm
    pdf.line(PAGE_WIDTH - RIGHT_MARGIN - qty_box_w, row_top + 12 * mm, PAGE_WIDTH - RIGHT_MARGIN - qty_box_w, row_top)
    pdf.line(PAGE_WIDTH - RIGHT_MARGIN - qty_box_w, row_top + 6 * mm, PAGE_WIDTH - RIGHT_MARGIN, row_top + 6 * mm)
    _draw_cell_text(pdf, PAGE_WIDTH - RIGHT_MARGIN - qty_box_w, row_top + 12 * mm, qty_box_w, 6 * mm, "Qty. Checked:", font_name="Helvetica-Bold")
    _draw_cell_text(pdf, PAGE_WIDTH - RIGHT_MARGIN - 20 * mm, row_top + 12 * mm, 18 * mm, 6 * mm, "")
    _draw_cell_text(pdf, PAGE_WIDTH - RIGHT_MARGIN - qty_box_w, row_top + 6 * mm, qty_box_w, 6 * mm, "Qty.", font_name="Helvetica-Bold")
    _draw_cell_text(pdf, PAGE_WIDTH - RIGHT_MARGIN - 20 * mm, row_top + 6 * mm, 18 * mm, 6 * mm, "")
    return row_top - 10 * mm


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


def build_process_report_template_pdf(*, invoice, report_date: date | None, part_name: str) -> bytes:
    context = _report_template_context(
        invoice=invoice,
        report_date=report_date,
        part_name=part_name,
        title="Process Report",
        subtitle="Heat Treatment Cycle Template",
    )
    return _render_html_pdf("reporting/pdf/process_report_template.html", context)


def build_inspection_report_template_pdf(*, invoice, report_date: date | None, part_name: str) -> bytes:
    context = _report_template_context(
        invoice=invoice,
        report_date=report_date,
        part_name=part_name,
        title="Heat Treatment Inspection Report",
        subtitle="Test Certificate Template",
    )
    return _render_html_pdf("reporting/pdf/inspection_report_template.html", context)
