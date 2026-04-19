from __future__ import annotations

from django import forms

from masters.models import Party


class LedgerFilterForm(forms.Form):
    party = forms.ModelChoiceField(queryset=Party.objects.filter(is_active=True).order_by("name"))
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))


class DateRangeForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
