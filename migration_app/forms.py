from __future__ import annotations

from django import forms

from migration_app.models import MigrationBatch, MigrationMappingProfile


class UploadImportForm(forms.Form):
    import_type = forms.ChoiceField(choices=MigrationBatch.ImportType.choices)
    profile = forms.ModelChoiceField(
        queryset=MigrationMappingProfile.objects.all(),
        required=False,
        help_text="Optional mapping profile for recurring file formats.",
    )
    upload = forms.FileField()


class ConfirmImportForm(forms.Form):
    token = forms.CharField(widget=forms.HiddenInput())
