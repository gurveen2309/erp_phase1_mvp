from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError

from finance.models import Invoice
from masters.models import Party

_CHAR = {"required": False}
_DATE = {"required": False, "widget": forms.DateInput(attrs={"type": "date"})}


class _PartyInvoiceMixin(forms.Form):
    party = forms.ModelChoiceField(queryset=Party.objects.filter(is_active=True).order_by("name"))
    invoice = forms.ModelChoiceField(
        queryset=Invoice.objects.select_related("party").order_by("-invoice_date"),
        required=False,
        empty_label="— None —",
    )

    def clean(self):
        cleaned = super().clean()
        party = cleaned.get("party")
        invoice = cleaned.get("invoice")
        if invoice and party and invoice.party_id != party.id:
            raise ValidationError("Selected invoice does not belong to the selected party.")
        return cleaned


class LedgerFilterForm(forms.Form):
    party = forms.ModelChoiceField(queryset=Party.objects.filter(is_active=True).order_by("name"))
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))


class DateRangeForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))


class ProcessReportForm(_PartyInvoiceMixin):
    ref_no = forms.CharField(**_CHAR, label="Ref. No.")
    dated = forms.DateField(**_DATE, label="Dated")
    date = forms.DateField(**_DATE, label="Date")
    part_name = forms.CharField(**_CHAR, label="Part Name / No.")
    hardness = forms.CharField(**_CHAR, label="Hardness")
    sample_id = forms.CharField(**_CHAR, label="Sample ID No.")
    material_grade = forms.CharField(**_CHAR, label="Material Grade")
    # Cycle table — one row
    size = forms.CharField(**_CHAR, label="Size")
    hardening_temp = forms.CharField(**_CHAR, label="Hardening Temp.")
    hardening_speed = forms.CharField(**_CHAR, label="Speed Mesh Belt (Hardening)")
    hardening_hrc = forms.CharField(**_CHAR, label="Hardening HRC")
    quenching_media = forms.CharField(**_CHAR, label="Quenching Media")
    quenching_temp = forms.CharField(**_CHAR, label="Quenching Temp.")
    tempering_temp = forms.CharField(**_CHAR, label="Tempering Temp.")
    tempering_speed = forms.CharField(**_CHAR, label="Speed Mesh Belt (Tempering)")
    tempering_hrc = forms.CharField(**_CHAR, label="Tempering HRC")


class InspectionReportForm(_PartyInvoiceMixin):
    date = forms.DateField(**_DATE, label="Date")
    part_name = forms.CharField(**_CHAR, label="Part Name")
    no = forms.CharField(**_CHAR, label="No.")
    lot_qty = forms.CharField(**_CHAR, label="Lot Qty")
    material_grade = forms.CharField(**_CHAR, label="Material Grade")
    supplier_tc_received = forms.CharField(**_CHAR, label="Supplier TC Received or Not")
    process_done = forms.CharField(**_CHAR, label="Process Done")
    ht = forms.CharField(**_CHAR, label="H/T")
    # Specification column per parameter
    hardness_spec = forms.CharField(**_CHAR, label="Hardness (Surface) — Spec")
    micro_structure_spec = forms.CharField(**_CHAR, label="Micro-Structure — Spec")
    grain_size_spec = forms.CharField(**_CHAR, label="Grain Size — Spec")
    tensile_strength_spec = forms.CharField(**_CHAR, label="Tensile Strength (MPa) — Spec")
    other_requirements_spec = forms.CharField(**_CHAR, label="Any Other Requirements — Spec")
    # 8 observation columns per parameter
    hardness_obs_1 = forms.CharField(**_CHAR, label="Obs 1")
    hardness_obs_2 = forms.CharField(**_CHAR, label="Obs 2")
    hardness_obs_3 = forms.CharField(**_CHAR, label="Obs 3")
    hardness_obs_4 = forms.CharField(**_CHAR, label="Obs 4")
    hardness_obs_5 = forms.CharField(**_CHAR, label="Obs 5")
    hardness_obs_6 = forms.CharField(**_CHAR, label="Obs 6")
    hardness_obs_7 = forms.CharField(**_CHAR, label="Obs 7")
    hardness_obs_8 = forms.CharField(**_CHAR, label="Obs 8")

    micro_structure_obs_1 = forms.CharField(**_CHAR, label="Obs 1")
    micro_structure_obs_2 = forms.CharField(**_CHAR, label="Obs 2")
    micro_structure_obs_3 = forms.CharField(**_CHAR, label="Obs 3")
    micro_structure_obs_4 = forms.CharField(**_CHAR, label="Obs 4")
    micro_structure_obs_5 = forms.CharField(**_CHAR, label="Obs 5")
    micro_structure_obs_6 = forms.CharField(**_CHAR, label="Obs 6")
    micro_structure_obs_7 = forms.CharField(**_CHAR, label="Obs 7")
    micro_structure_obs_8 = forms.CharField(**_CHAR, label="Obs 8")

    grain_size_obs_1 = forms.CharField(**_CHAR, label="Obs 1")
    grain_size_obs_2 = forms.CharField(**_CHAR, label="Obs 2")
    grain_size_obs_3 = forms.CharField(**_CHAR, label="Obs 3")
    grain_size_obs_4 = forms.CharField(**_CHAR, label="Obs 4")
    grain_size_obs_5 = forms.CharField(**_CHAR, label="Obs 5")
    grain_size_obs_6 = forms.CharField(**_CHAR, label="Obs 6")
    grain_size_obs_7 = forms.CharField(**_CHAR, label="Obs 7")
    grain_size_obs_8 = forms.CharField(**_CHAR, label="Obs 8")

    tensile_strength_obs_1 = forms.CharField(**_CHAR, label="Obs 1")
    tensile_strength_obs_2 = forms.CharField(**_CHAR, label="Obs 2")
    tensile_strength_obs_3 = forms.CharField(**_CHAR, label="Obs 3")
    tensile_strength_obs_4 = forms.CharField(**_CHAR, label="Obs 4")
    tensile_strength_obs_5 = forms.CharField(**_CHAR, label="Obs 5")
    tensile_strength_obs_6 = forms.CharField(**_CHAR, label="Obs 6")
    tensile_strength_obs_7 = forms.CharField(**_CHAR, label="Obs 7")
    tensile_strength_obs_8 = forms.CharField(**_CHAR, label="Obs 8")

    other_obs_1 = forms.CharField(**_CHAR, label="Obs 1")
    other_obs_2 = forms.CharField(**_CHAR, label="Obs 2")
    other_obs_3 = forms.CharField(**_CHAR, label="Obs 3")
    other_obs_4 = forms.CharField(**_CHAR, label="Obs 4")
    other_obs_5 = forms.CharField(**_CHAR, label="Obs 5")
    other_obs_6 = forms.CharField(**_CHAR, label="Obs 6")
    other_obs_7 = forms.CharField(**_CHAR, label="Obs 7")
    other_obs_8 = forms.CharField(**_CHAR, label="Obs 8")

    qty_checked = forms.CharField(**_CHAR, label="Qty. Checked")
    qty = forms.CharField(**_CHAR, label="Qty.")
