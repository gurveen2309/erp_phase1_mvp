from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.db import connections, transaction
from django.utils import timezone

from governance.models import ApprovalRequest, AuditEvent, BackupSnapshot


SNAPSHOT_EXCLUDE_FIELDS = {"id", "created_at", "updated_at"}


def serialize_instance(instance) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for field in instance._meta.concrete_fields:
        if field.name in SNAPSHOT_EXCLUDE_FIELDS:
            continue
        snapshot[field.name] = getattr(instance, field.attname)
    return snapshot


def apply_snapshot(instance, snapshot: dict[str, Any]) -> None:
    for field in instance._meta.concrete_fields:
        if field.name in SNAPSHOT_EXCLUDE_FIELDS or field.primary_key:
            continue
        if field.name in snapshot:
            setattr(instance, field.attname, snapshot[field.name])


def get_content_type_for_model(model_class):
    return ContentType.objects.get_for_model(model_class)


def log_audit(
    event_type: str,
    *,
    actor=None,
    obj=None,
    approval_request: ApprovalRequest | None = None,
    migration_batch=None,
    before_snapshot: dict[str, Any] | None = None,
    after_snapshot: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    content_type=None,
    object_id=None,
    object_repr: str = "",
) -> AuditEvent:
    if obj is not None:
        content_type = get_content_type_for_model(obj.__class__)
        object_id = obj.pk
        object_repr = str(obj)
    elif content_type and object_id and not object_repr:
        model_class = content_type.model_class()
        object_repr = f"{model_class._meta.verbose_name.title()} #{object_id}"

    return AuditEvent.objects.create(
        event_type=event_type,
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        approval_request=approval_request,
        migration_batch=migration_batch,
        before_snapshot=before_snapshot or {},
        after_snapshot=after_snapshot or {},
        metadata=metadata or {},
        content_type=content_type,
        object_id=object_id,
        object_repr=object_repr,
    )


def create_approval_request(
    *,
    action_type: str,
    submitted_by,
    model_class=None,
    object_id: int | None = None,
    before_snapshot: dict[str, Any] | None = None,
    after_snapshot: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    reason: str = "",
    comments: str = "",
    upload_name: str | None = None,
    upload_bytes: bytes | None = None,
) -> ApprovalRequest:
    request_obj = ApprovalRequest.objects.create(
        content_type=get_content_type_for_model(model_class) if model_class else None,
        object_id=object_id,
        action_type=action_type,
        submitted_by=submitted_by if getattr(submitted_by, "is_authenticated", False) else None,
        before_snapshot=before_snapshot or {},
        after_snapshot=after_snapshot or {},
        metadata=metadata or {},
        reason=reason,
        comments=comments,
    )
    if upload_name and upload_bytes is not None:
        request_obj.upload.save(upload_name, ContentFile(upload_bytes), save=True)
    log_audit(
        "approval.submitted",
        actor=submitted_by,
        approval_request=request_obj,
        before_snapshot=before_snapshot,
        after_snapshot=after_snapshot,
        metadata={"action_type": action_type, **(metadata or {})},
        content_type=request_obj.content_type,
        object_id=request_obj.object_id,
    )
    return request_obj


def reject_approval_request(request_obj: ApprovalRequest, actor, comments: str = "") -> ApprovalRequest:
    request_obj.status = ApprovalRequest.Status.REJECTED
    request_obj.approved_by = actor if getattr(actor, "is_authenticated", False) else None
    request_obj.rejected_at = timezone.now()
    request_obj.comments = comments
    request_obj.save(update_fields=["status", "approved_by", "rejected_at", "comments", "updated_at"])
    log_audit(
        "approval.rejected",
        actor=actor,
        approval_request=request_obj,
        before_snapshot=request_obj.before_snapshot,
        after_snapshot=request_obj.after_snapshot,
        metadata={"comments": comments},
        content_type=request_obj.content_type,
        object_id=request_obj.object_id,
    )
    return request_obj


def _model_class_from_request(request_obj: ApprovalRequest):
    return request_obj.content_type.model_class() if request_obj.content_type else None


def _db_env() -> dict[str, str]:
    db = settings.DATABASES["default"]
    return {
        **os.environ,
        "PGPASSWORD": db.get("PASSWORD", ""),
    }


def _backup_root() -> Path:
    root = Path(settings.BACKUP_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _maintenance_lock_path() -> Path:
    return Path(settings.MAINTENANCE_MODE_FILE)


def create_backup_snapshot(*, actor=None, backup_type: str = BackupSnapshot.BackupType.MANUAL, notes: str = "", approval_request=None) -> BackupSnapshot:
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    root = _backup_root()
    file_path = root / f"db_{timestamp}.sql"
    snapshot = BackupSnapshot.objects.create(
        backup_type=backup_type,
        file_path=str(file_path),
        status=BackupSnapshot.Status.PENDING,
        created_by=actor if getattr(actor, "is_authenticated", False) else None,
        notes=notes,
    )
    db = settings.DATABASES["default"]
    try:
        with file_path.open("wb") as handle:
            subprocess.run(
                [
                    "pg_dump",
                    "-h",
                    db.get("HOST", "postgres"),
                    "-p",
                    str(db.get("PORT", "5432")),
                    "-U",
                    db.get("USER", "erp"),
                    db.get("NAME", "erp_phase1"),
                ],
                check=True,
                stdout=handle,
                env=_db_env(),
            )
        snapshot.file_size = file_path.stat().st_size
        snapshot.status = BackupSnapshot.Status.COMPLETED
        snapshot.save(update_fields=["file_size", "status"])
        log_audit(
            "backup.created",
            actor=actor,
            approval_request=approval_request,
            after_snapshot={"backup_snapshot_id": snapshot.id, "file_path": snapshot.file_path},
            metadata={"backup_type": backup_type},
        )
    except subprocess.CalledProcessError as exc:
        snapshot.status = BackupSnapshot.Status.FAILED
        snapshot.notes = "\n".join(part for part in [snapshot.notes, f"Backup failed: {exc}"] if part)
        snapshot.save(update_fields=["status", "notes"])
        log_audit(
            "backup.failed",
            actor=actor,
            approval_request=approval_request,
            after_snapshot={"backup_snapshot_id": snapshot.id},
            metadata={"error": str(exc)},
        )
        raise
    return snapshot


def restore_backup_snapshot(snapshot: BackupSnapshot, *, actor=None, approval_request=None, notes: str = "") -> BackupSnapshot:
    pre_restore = create_backup_snapshot(
        actor=actor,
        backup_type=BackupSnapshot.BackupType.PRE_RESTORE,
        notes=f"Pre-restore backup before restoring snapshot {snapshot.id}. {notes}".strip(),
        approval_request=approval_request,
    )
    db = settings.DATABASES["default"]
    lock_path = _maintenance_lock_path()
    lock_path.write_text(f"restore_started_at={timezone.now().isoformat()}\n")
    log_audit(
        "backup.restore.started",
        actor=actor,
        approval_request=approval_request,
        after_snapshot={"backup_snapshot_id": snapshot.id, "pre_restore_backup_id": pre_restore.id},
        metadata={"notes": notes},
    )
    try:
        connections.close_all()
        subprocess.run(
            [
                "psql",
                "-h",
                db.get("HOST", "postgres"),
                "-p",
                str(db.get("PORT", "5432")),
                "-U",
                db.get("USER", "erp"),
                "-d",
                db.get("NAME", "erp_phase1"),
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                "DROP SCHEMA public CASCADE; CREATE SCHEMA public;",
            ],
            check=True,
            env=_db_env(),
        )
        subprocess.run(
            [
                "psql",
                "-h",
                db.get("HOST", "postgres"),
                "-p",
                str(db.get("PORT", "5432")),
                "-U",
                db.get("USER", "erp"),
                "-d",
                db.get("NAME", "erp_phase1"),
                "-v",
                "ON_ERROR_STOP=1",
                "-f",
                snapshot.file_path,
            ],
            check=True,
            env=_db_env(),
        )
        snapshot.status = BackupSnapshot.Status.RESTORED
        snapshot.restored_at = timezone.now()
        snapshot.notes = "\n".join(part for part in [snapshot.notes, notes] if part)
        snapshot.save(update_fields=["status", "restored_at", "notes"])
        log_audit(
            "backup.restore.completed",
            actor=actor,
            approval_request=approval_request,
            after_snapshot={"backup_snapshot_id": snapshot.id},
            metadata={"pre_restore_backup_id": pre_restore.id},
        )
    except subprocess.CalledProcessError as exc:
        snapshot.status = BackupSnapshot.Status.FAILED
        snapshot.notes = "\n".join(part for part in [snapshot.notes, f"Restore failed: {exc}", notes] if part)
        snapshot.save(update_fields=["status", "notes"])
        log_audit(
            "backup.restore.failed",
            actor=actor,
            approval_request=approval_request,
            after_snapshot={"backup_snapshot_id": snapshot.id},
            metadata={"error": str(exc), "pre_restore_backup_id": pre_restore.id},
        )
        raise
    finally:
        if lock_path.exists():
            lock_path.unlink()
    return snapshot


def rollback_import_batch(batch, *, actor=None, approval_request=None, notes: str = ""):
    from masters.models import Party
    from finance.models import Invoice, OpeningBalance, Payment
    from production.models import Challan

    if batch.status == batch.Status.ROLLED_BACK:
        return batch

    log_audit(
        "import.rollback.started",
        actor=actor,
        approval_request=approval_request,
        migration_batch=batch,
        after_snapshot={"batch_id": batch.id},
        metadata={"notes": notes},
    )
    with transaction.atomic():
        Challan.objects.filter(source_batch=batch).delete()
        Payment.objects.filter(source_batch=batch).delete()
        Invoice.objects.filter(source_batch=batch).delete()
        OpeningBalance.objects.filter(source_batch=batch).delete()
        for party in Party.objects.filter(source_batch=batch):
            if not party.challans.exists() and not party.invoices.exists() and not party.payments.exists() and not party.opening_balances.exists():
                party.delete()
        batch.status = batch.Status.ROLLED_BACK
        batch.rolled_back_at = timezone.now()
        batch.rolled_back_by = actor if getattr(actor, "is_authenticated", False) else None
        batch.rollback_notes = notes
        batch.save(update_fields=["status", "rolled_back_at", "rolled_back_by", "rollback_notes"])
    log_audit(
        "import.rollback.completed",
        actor=actor,
        approval_request=approval_request,
        migration_batch=batch,
        after_snapshot={"batch_id": batch.id},
        metadata={"notes": notes},
    )
    return batch


def execute_approval_request(request_obj: ApprovalRequest, actor, comments: str = "") -> ApprovalRequest:
    from migration_app.models import MigrationBatch
    from migration_app.services import commit_preview, deserialize_preview

    request_obj.status = ApprovalRequest.Status.APPROVED
    request_obj.approved_by = actor if getattr(actor, "is_authenticated", False) else None
    request_obj.approved_at = timezone.now()
    request_obj.comments = comments
    request_obj.save(update_fields=["status", "approved_by", "approved_at", "comments", "updated_at"])
    log_audit(
        "approval.approved",
        actor=actor,
        approval_request=request_obj,
        before_snapshot=request_obj.before_snapshot,
        after_snapshot=request_obj.after_snapshot,
        metadata={"comments": comments},
        content_type=request_obj.content_type,
        object_id=request_obj.object_id,
    )

    model_class = _model_class_from_request(request_obj)
    try:
        if request_obj.action_type == ApprovalRequest.ActionType.CREATE:
            obj = model_class()
            apply_snapshot(obj, request_obj.after_snapshot)
            obj.save()
            request_obj.object_id = obj.pk
            log_audit(
                "finance.create.executed",
                actor=actor,
                obj=obj,
                approval_request=request_obj,
                after_snapshot=serialize_instance(obj),
            )
        elif request_obj.action_type == ApprovalRequest.ActionType.UPDATE:
            obj = model_class.objects.get(pk=request_obj.object_id)
            before_snapshot = serialize_instance(obj)
            apply_snapshot(obj, request_obj.after_snapshot)
            obj.save()
            log_audit(
                "finance.update.executed",
                actor=actor,
                obj=obj,
                approval_request=request_obj,
                before_snapshot=before_snapshot,
                after_snapshot=serialize_instance(obj),
            )
        elif request_obj.action_type == ApprovalRequest.ActionType.DELETE:
            obj = model_class.objects.get(pk=request_obj.object_id)
            before_snapshot = serialize_instance(obj)
            content_type = get_content_type_for_model(model_class)
            object_id = obj.pk
            object_repr = str(obj)
            obj.delete()
            log_audit(
                "finance.delete.executed",
                actor=actor,
                approval_request=request_obj,
                content_type=content_type,
                object_id=object_id,
                object_repr=object_repr,
                before_snapshot=before_snapshot,
            )
        elif request_obj.action_type == ApprovalRequest.ActionType.IMPORT_COMMIT:
            preview = deserialize_preview(request_obj.after_snapshot["preview"])
            upload_bytes = request_obj.upload.read() if request_obj.upload else b""
            batch = commit_preview(preview, upload_bytes, actor)
            request_obj.content_type = get_content_type_for_model(MigrationBatch)
            request_obj.object_id = batch.id
            log_audit(
                "import.commit.executed",
                actor=actor,
                approval_request=request_obj,
                migration_batch=batch,
                after_snapshot={"batch_id": batch.id, "success_count": batch.success_count},
            )
        elif request_obj.action_type == ApprovalRequest.ActionType.IMPORT_ROLLBACK:
            batch = apps.get_model("migration_app", "MigrationBatch").objects.get(pk=request_obj.after_snapshot["batch_id"])
            rollback_import_batch(batch, actor=actor, approval_request=request_obj, notes=comments)
            request_obj.content_type = get_content_type_for_model(batch.__class__)
            request_obj.object_id = batch.id
        elif request_obj.action_type == ApprovalRequest.ActionType.BACKUP_RESTORE:
            snapshot = BackupSnapshot.objects.get(pk=request_obj.after_snapshot["backup_snapshot_id"])
            restore_backup_snapshot(snapshot, actor=actor, approval_request=request_obj, notes=comments)
        else:
            raise ValueError(f"Unsupported approval action '{request_obj.action_type}'")
        request_obj.status = ApprovalRequest.Status.EXECUTED
        request_obj.executed_at = timezone.now()
        request_obj.execution_error = ""
    except Exception as exc:
        request_obj.execution_error = str(exc)
        request_obj.save(update_fields=["execution_error", "updated_at"])
        raise

    request_obj.save(
        update_fields=[
            "status",
            "executed_at",
            "execution_error",
            "content_type",
            "object_id",
            "updated_at",
        ]
    )
    log_audit(
        "approval.executed",
        actor=actor,
        approval_request=request_obj,
        before_snapshot=request_obj.before_snapshot,
        after_snapshot=request_obj.after_snapshot,
        metadata={"action_type": request_obj.action_type},
        content_type=request_obj.content_type,
        object_id=request_obj.object_id,
    )
    return request_obj
