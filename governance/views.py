from __future__ import annotations

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect, render

from governance.forms import ApprovalDecisionForm, BackupCreateForm, RestoreBackupForm
from governance.models import ApprovalRequest, AuditEvent, BackupSnapshot
from governance.services import create_backup_snapshot, execute_approval_request, reject_approval_request, restore_backup_snapshot


@staff_member_required
@permission_required("governance.approve_finance_change", raise_exception=True)
def approval_queue_view(request):
    return render(
        request,
        "governance/approval_queue.html",
        {
            "pending_requests": ApprovalRequest.objects.filter(status=ApprovalRequest.Status.PENDING),
            "recent_requests": ApprovalRequest.objects.exclude(status=ApprovalRequest.Status.PENDING)[:25],
        },
    )


@staff_member_required
@permission_required("governance.approve_finance_change", raise_exception=True)
def approval_detail_view(request, request_id: int):
    approval_request = get_object_or_404(ApprovalRequest, pk=request_id)
    form = ApprovalDecisionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        action = request.POST.get("action")
        if action == "approve":
            execute_approval_request(approval_request, request.user, comments=form.cleaned_data["comments"])
            messages.success(request, "Approval request executed.")
        elif action == "reject":
            reject_approval_request(approval_request, request.user, comments=form.cleaned_data["comments"])
            messages.success(request, "Approval request rejected.")
        return redirect("governance:approval-queue")

    return render(
        request,
        "governance/approval_detail.html",
        {
            "approval_request": approval_request,
            "form": form,
        },
    )


@staff_member_required
@permission_required("governance.view_audit_log", raise_exception=True)
def audit_log_view(request):
    return render(
        request,
        "governance/audit_log.html",
        {
            "events": AuditEvent.objects.select_related("actor", "approval_request", "migration_batch")[:200],
        },
    )


@staff_member_required
@permission_required("governance.create_db_backup", raise_exception=True)
def backup_list_view(request):
    form = BackupCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        create_backup_snapshot(actor=request.user, notes=form.cleaned_data["notes"])
        messages.success(request, "Database backup created.")
        return redirect("governance:backups")

    return render(
        request,
        "governance/backup_list.html",
        {
            "form": form,
            "snapshots": BackupSnapshot.objects.all(),
        },
    )


@staff_member_required
@permission_required("governance.restore_db_backup", raise_exception=True)
def restore_backup_view(request, snapshot_id: int):
    snapshot = get_object_or_404(BackupSnapshot, pk=snapshot_id)
    form = RestoreBackupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        restore_backup_snapshot(snapshot, actor=request.user, notes=form.cleaned_data["notes"])
        messages.success(request, "Backup restore executed.")
        return redirect("governance:backups")

    return render(
        request,
        "governance/restore_backup.html",
        {
            "snapshot": snapshot,
            "form": form,
        },
    )
