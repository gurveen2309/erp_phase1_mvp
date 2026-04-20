from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ApprovalRequest(models.Model):
    class ActionType(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        IMPORT_COMMIT = "import_commit", "Import Commit"
        IMPORT_ROLLBACK = "import_rollback", "Import Rollback"
        BACKUP_RESTORE = "backup_restore", "Backup Restore"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        EXECUTED = "executed", "Executed"
        CANCELLED = "cancelled", "Cancelled"

    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target_object = GenericForeignKey("content_type", "object_id")
    action_type = models.CharField(max_length=40, choices=ActionType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="submitted_approval_requests",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_approval_requests",
    )
    before_snapshot = models.JSONField(default=dict, blank=True)
    after_snapshot = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    upload = models.FileField(upload_to="approval_requests/%Y/%m/%d/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    execution_error = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        permissions = [
            ("approve_finance_change", "Can approve finance change requests"),
            ("approve_import_commit", "Can approve import commits"),
            ("rollback_import_batch", "Can roll back imported batches"),
        ]

    def __str__(self) -> str:
        label = self.content_type.model_class()._meta.verbose_name.title() if self.content_type else "System"
        return f"{label} {self.get_action_type_display()} ({self.get_status_display()})"


class BackupSnapshot(models.Model):
    class BackupType(models.TextChoices):
        MANUAL = "manual", "Manual"
        PRE_RESTORE = "pre_restore", "Pre-Restore"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        RESTORED = "restored", "Restored"

    backup_type = models.CharField(max_length=20, choices=BackupType.choices, default=BackupType.MANUAL)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_backup_snapshots",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    restored_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        permissions = [
            ("create_db_backup", "Can create database backups"),
            ("restore_db_backup", "Can restore database backups"),
        ]

    def __str__(self) -> str:
        return f"{self.get_backup_type_display()} backup ({self.get_status_display()})"


class AuditEvent(models.Model):
    event_type = models.CharField(max_length=80)
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target_object = GenericForeignKey("content_type", "object_id")
    object_repr = models.CharField(max_length=255, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    approval_request = models.ForeignKey(
        "governance.ApprovalRequest",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    migration_batch = models.ForeignKey(
        "migration_app.MigrationBatch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    before_snapshot = models.JSONField(default=dict, blank=True)
    after_snapshot = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at", "-id"]
        permissions = [
            ("view_audit_log", "Can view audit log"),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.occurred_at:%Y-%m-%d %H:%M:%S}"

