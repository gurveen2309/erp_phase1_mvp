from __future__ import annotations

import base64
import csv
import io

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from migration_app.forms import ConfirmImportForm, UploadImportForm
from migration_app.models import MigrationBatch, MigrationMappingProfile
from migration_app.services import build_preview, commit_preview, deserialize_preview, serialize_preview


SESSION_KEY = "erp_import_preview"
SESSION_UPLOAD = "erp_import_upload"


@staff_member_required
def upload_import_view(request):
    preview = None
    if request.method == "POST":
        form = UploadImportForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.cleaned_data["profile"]
            if profile and profile.import_type != form.cleaned_data["import_type"]:
                form.add_error("profile", "Selected profile does not match import type.")
            else:
                upload = form.cleaned_data["upload"]
                upload_bytes = upload.read()
                upload.seek(0)
                try:
                    preview = build_preview(upload, form.cleaned_data["import_type"], profile)
                except ValueError as exc:
                    form.add_error("upload", str(exc))
                else:
                    request.session[SESSION_KEY] = serialize_preview(preview)
                    request.session[SESSION_UPLOAD] = base64.b64encode(upload_bytes).decode("ascii")
    else:
        form = UploadImportForm()
        stored_preview = request.session.get(SESSION_KEY)
        if stored_preview:
            preview = deserialize_preview(stored_preview)

    return render(
        request,
        "migration_app/upload_import.html",
        {
            "form": form,
            "preview": preview,
            "confirm_form": ConfirmImportForm(initial={"token": preview.token}) if preview else None,
        },
    )


@staff_member_required
def confirm_import_view(request):
    form = ConfirmImportForm(request.POST or None)
    if request.method != "POST" or not form.is_valid():
        return redirect("migration_app:upload")

    stored_preview = request.session.get(SESSION_KEY)
    stored_upload = request.session.get(SESSION_UPLOAD)
    if not stored_preview or not stored_upload:
        messages.error(request, "No import preview is available.")
        return redirect("migration_app:upload")

    preview = deserialize_preview(stored_preview)
    if preview.token != form.cleaned_data["token"]:
        messages.error(request, "Import preview token mismatch. Please preview again.")
        return redirect("migration_app:upload")

    batch = commit_preview(preview, base64.b64decode(stored_upload), request.user)
    request.session.pop(SESSION_KEY, None)
    request.session.pop(SESSION_UPLOAD, None)
    messages.success(request, f"Imported {batch.success_count} rows with {batch.error_count} validation errors retained.")
    return redirect("migration_app:history")


@staff_member_required
def batch_history_view(request):
    return render(
        request,
        "migration_app/batch_history.html",
        {
            "batches": MigrationBatch.objects.prefetch_related("row_errors").all(),
        },
    )


@staff_member_required
def download_errors_view(request, batch_id: int):
    batch = get_object_or_404(MigrationBatch, pk=batch_id)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["row_number", "sheet_name", "error_message", "raw_payload"])
    for error in batch.row_errors.all():
        writer.writerow([error.row_number, error.sheet_name, error.error_message, error.raw_payload])

    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="batch_{batch.id}_errors.csv"'
    return response
