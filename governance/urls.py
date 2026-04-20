from django.urls import path

from governance import views


app_name = "governance"

urlpatterns = [
    path("approvals/", views.approval_queue_view, name="approval-queue"),
    path("approvals/<int:request_id>/", views.approval_detail_view, name="approval-detail"),
    path("audit/", views.audit_log_view, name="audit-log"),
    path("backups/", views.backup_list_view, name="backups"),
    path("backups/<int:snapshot_id>/restore/", views.restore_backup_view, name="restore-backup"),
]

