from django.contrib import admin

from governance.models import ApprovalRequest, AuditEvent, BackupSnapshot


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "action_type", "status", "content_type", "object_id", "submitted_by", "approved_by", "created_at")
    list_filter = ("action_type", "status", "content_type")
    search_fields = ("reason", "comments", "execution_error")
    readonly_fields = (
        "content_type",
        "object_id",
        "submitted_by",
        "approved_by",
        "before_snapshot",
        "after_snapshot",
        "metadata",
        "reason",
        "comments",
        "upload",
        "created_at",
        "updated_at",
        "approved_at",
        "rejected_at",
        "executed_at",
        "execution_error",
    )

    def has_add_permission(self, request):
        return False


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "event_type", "actor", "object_repr", "migration_batch")
    list_filter = ("event_type", "content_type")
    search_fields = ("object_repr", "metadata")
    readonly_fields = (
        "event_type",
        "content_type",
        "object_id",
        "object_repr",
        "actor",
        "approval_request",
        "migration_batch",
        "before_snapshot",
        "after_snapshot",
        "metadata",
        "occurred_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BackupSnapshot)
class BackupSnapshotAdmin(admin.ModelAdmin):
    list_display = ("id", "backup_type", "status", "file_path", "file_size", "created_by", "created_at", "restored_at")
    list_filter = ("backup_type", "status")
    search_fields = ("file_path", "notes")
    readonly_fields = ("file_path", "file_size", "created_by", "created_at", "restored_at")

    def has_delete_permission(self, request, obj=None):
        return False

